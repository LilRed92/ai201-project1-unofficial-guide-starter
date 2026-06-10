"""
Milestone 5 — Generation (grounded answering)
The Unofficial Guide to Band Lore and Concert Culture

Takes a question plus the chunks retrieved in Milestone 4 and asks Groq's
`llama-3.3-70b-versatile` to answer using ONLY those chunks. Source
attribution is appended programmatically — never left to the model.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from groq import Groq

# Load GROQ_API_KEY from .env (kept out of git via .gitignore).
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# planning.md specifies this Groq model for generation.
GROQ_MODEL = "llama-3.3-70b-versatile"

# Exact message returned when the documents can't answer the question. The
# system prompt instructs the model to emit this verbatim, and query.py also
# returns it directly when retrieval is too weak (defence in depth).
FALLBACK_MESSAGE = (
    "I don't have enough information on that topic in the available documents."
)

# Grounding is enforced, not suggested: "ONLY", an explicit refusal rule, and a
# fixed fallback string the rest of the pipeline can detect.
SYSTEM_PROMPT = (
    "You are a helpful assistant for a guide about band lore and concert "
    "culture. Answer the user's question using ONLY the information provided "
    "in the documents below. Do not use any outside knowledge, and do not "
    "make assumptions beyond what the documents state. If the documents do "
    "not contain enough information to answer the question, respond with "
    f'exactly: "{FALLBACK_MESSAGE}"'
)

# Lazily-initialised Groq client (created once, after the key is confirmed).
_client: Groq | None = None


def get_client() -> Groq:
    """Return a Groq client, creating it on first use.

    Prints a one-time startup message confirming the model and that the key is
    loaded, with all but the last 4 characters of the key masked.
    """
    global _client
    if _client is None:
        if not GROQ_API_KEY or GROQ_API_KEY == "your_key_here":
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file "
                "(get a free key at https://console.groq.com)."
            )
        masked = "*" * (len(GROQ_API_KEY) - 4) + GROQ_API_KEY[-4:]
        print(f"[generation] Groq client ready | model={GROQ_MODEL} | key={masked}")
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def _format_context(chunks: list[dict]) -> str:
    """Format retrieved chunks as labelled context blocks for the prompt.

    Each chunk is prefaced with its source filename so the model can ground
    its answer in specific documents.
    """
    blocks = []
    for chunk in chunks:
        blocks.append(f"[Source: {chunk['source']}]\n{chunk['text']}")
    return "\n\n".join(blocks)


def generate(query: str, chunks: list[dict]) -> dict:
    """
    Send retrieved chunks + query to the LLM.
    Returns {"answer": str, "sources": list[str], "chunks_used": int}
    """
    # Deduplicated source filenames, attached programmatically (not via the LLM).
    sources = sorted({chunk["source"] for chunk in chunks})

    # No chunks -> don't even call the model; the answer can't be grounded.
    if not chunks:
        return {"answer": FALLBACK_MESSAGE, "sources": [], "chunks_used": 0}

    context = _format_context(chunks)
    user_message = (
        f"Documents:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer using only the documents above."
    )

    client = get_client()
    # temperature=0 keeps the answer deterministic and tied to the context,
    # which is what we want for grounded retrieval rather than creative text.
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
    )
    answer = completion.choices[0].message.content.strip()

    return {"answer": answer, "sources": sources, "chunks_used": len(chunks)}
