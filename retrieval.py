"""
Milestone 4 — Embedding & Retrieval
The Unofficial Guide to Band Lore and Concert Culture

Takes the chunks produced by the Milestone 3 ingestion pipeline
(`chunk_documents.load_and_chunk`), embeds them locally with
`all-MiniLM-L6-v2`, stores them in a persistent ChromaDB collection, and
exposes a `retrieve(query, k)` function for similarity search.

All embedding/vector-store logic lives here, separate from ingestion.

Run directly to (re)build the index and run the evaluation queries:
    .venv/bin/python retrieval.py
"""

from __future__ import annotations

import chromadb
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer

from chunk_documents import Chunk, load_and_chunk

# --- Configuration -----------------------------------------------------------
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"   # local, no API key, no rate limits
CHROMA_PATH = "./chroma_db"             # persistent store (survives between runs)
COLLECTION_NAME = "band_lore"
# planning.md specifies top-k = 4 for the final system; the Milestone 4 spec
# tests with k = 5, so 5 is the default here. Change DEFAULT_TOP_K to tune it.
DEFAULT_TOP_K = 5

# Lazily-initialised singleton so the model is only loaded once per process.
_model: SentenceTransformer | None = None


# --- Embedding model ---------------------------------------------------------
def get_model() -> SentenceTransformer:
    """Load (once) and return the local SentenceTransformer embedding model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


# --- ChromaDB collection -----------------------------------------------------
def get_collection() -> Collection:
    """Open (or create) the persistent ChromaDB collection.

    `hnsw:space="cosine"` tells Chroma to score distance as **cosine distance**
    (0.0 = identical direction, ~1.0 = unrelated, up to 2.0 = opposite). The
    default space is L2 (squared Euclidean), whose raw magnitudes aren't
    comparable to the < 0.5 relevance threshold the evaluation uses — so we set
    cosine explicitly to make the distance scores interpretable.
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _to_record(chunk: Chunk | dict) -> tuple[str, str, int, str]:
    """Normalise a chunk (Chunk dataclass or dict) to (id, source, index, text).

    The id is deterministic (`<source>_chunk_<index>`) so re-running the build
    never creates duplicates for the same chunk.
    """
    if isinstance(chunk, dict):
        source = chunk["source"]
        index = int(chunk.get("chunk_index", 0))
        text = chunk["text"]
    else:  # Chunk dataclass from the ingestion pipeline
        source = chunk.source
        index = int(chunk.chunk_index)
        text = chunk.text
    return f"{source}_chunk_{index}", source, index, text


def build_index(chunks: list[Chunk] | list[dict] | None = None) -> Collection:
    """Embed all chunks and load them into ChromaDB, skipping any already stored.

    If `chunks` is None, the chunks are pulled straight from the ingestion
    pipeline (`load_and_chunk`) — no document paths are hardcoded here. Because
    ids are deterministic, running this repeatedly only embeds chunks that
    aren't in the collection yet, so there are no duplicate inserts.
    """
    if chunks is None:
        chunks = load_and_chunk()

    collection = get_collection()
    model = get_model()

    ids, sources, indices, documents = [], [], [], []
    for chunk in chunks:
        cid, source, index, text = _to_record(chunk)
        ids.append(cid)
        sources.append(source)
        indices.append(index)
        documents.append(text)

    # Ask the collection which of these ids already exist; only add the rest.
    # collection.get(ids=...) returns just the ids that are actually present.
    already_present = set(collection.get(ids=ids)["ids"])
    new = [i for i, cid in enumerate(ids) if cid not in already_present]

    if new:
        new_documents = [documents[i] for i in new]
        # encode() returns a numpy array; Chroma wants plain lists.
        embeddings = model.encode(new_documents, show_progress_bar=False).tolist()
        collection.add(
            ids=[ids[i] for i in new],
            embeddings=embeddings,
            documents=new_documents,
            metadatas=[
                {"source": sources[i], "chunk_index": indices[i]} for i in new
            ],
        )

    # --- Summary ---
    print(f"Collection '{COLLECTION_NAME}' now holds {collection.count()} chunks "
          f"({len(new)} newly embedded, {len(ids) - len(new)} already present).")
    sample = collection.get(ids=[ids[0]], include=["metadatas"])
    print(f"Sample metadata: {sample['metadatas'][0]}")
    return collection


# --- Retrieval ---------------------------------------------------------------
def retrieve(query: str, k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Given a query string, return the top-k most relevant chunks.

    Each returned dict contains:
      - "text":        the chunk content
      - "source":      the source document filename
      - "chunk_index": position in the source document
      - "distance":    cosine distance (lower = more relevant; < 0.5 is a good match)

    Tuning k: raise it for broader coverage when an answer is spread across
    several comments (at the cost of pulling in more off-topic context);
    lower it for tight, focused context. planning.md targets k = 4.
    """
    model = get_model()
    collection = get_collection()

    query_embedding = model.encode([query]).tolist()
    response = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Chroma nests results one level per query; we only sent one query -> [0].
    results: list[dict] = []
    for text, meta, distance in zip(
        response["documents"][0],
        response["metadatas"][0],
        response["distances"][0],
    ):
        results.append({
            "text": text,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "distance": distance,
        })
    return results


# --- Evaluation / retrieval-quality test -------------------------------------
# The 5 test queries from the Evaluation Plan in planning.md.
EVAL_QUERIES = [
    "According to the community lore, what physical trait is shared by all "
    "Papas from the Emeritus bloodline?",
    "What does Vessel waking up in a hospital in the song Atlantic signify "
    "about his connection to Sleep?",
    "Who is Cardinal Copia in relation to Papa Nihil before he becomes Papa "
    "Emeritus IV?",
    "What is the etiquette for a metal fan who wants to be near the stage but "
    "avoid moshing?",
    "What advice do veteran fans give about using your cell phone at Sleep "
    "Token concerts?",
]

RELEVANCE_THRESHOLD = 0.5  # cosine distance below this = a strong match


def _run_eval(k: int = DEFAULT_TOP_K) -> None:
    """Run the evaluation queries and print results + a debug summary."""
    passed = 0
    for query in EVAL_QUERIES:
        results = retrieve(query, k=k)
        print(f'Query: "{query}"\n')
        for rank, r in enumerate(results, start=1):
            print(f"Rank {rank} | Distance: {r['distance']:.4f} | "
                  f"Source: {r['source']} | Chunk: {r['chunk_index']}")
            print(r["text"])
            print()
        top_distance = results[0]["distance"] if results else float("inf")
        if top_distance < RELEVANCE_THRESHOLD:
            passed += 1
        print("-" * 80 + "\n")

    # --- Retrieval debug summary ---
    print("=" * 80)
    print("RETRIEVAL DEBUG SUMMARY")
    print("=" * 80)
    print(f"Queries with top result under {RELEVANCE_THRESHOLD} cosine distance: "
          f"{passed}/{len(EVAL_QUERIES)}")
    print("Checks: Relevance, distance scores (<0.5 = strong), source correctness, "
          "chunk completeness, coverage.")
    if passed >= 3:
        print("PASS: at least 3 queries return strong, relevant top results. "
              "OK to proceed to Milestone 5 (generation).")
    else:
        print("REVIEW NEEDED: fewer than 3 strong top results — inspect chunk "
              "size / metadata / embeddings before generation.")


if __name__ == "__main__":
    build_index()
    print()
    _run_eval()
