"""
Milestone 5 — RAG pipeline entry point
The Unofficial Guide to Band Lore and Concert Culture

`ask(question, k)` ties retrieval (Milestone 4) to grounded generation
(Milestone 5). This is the single function the Gradio interface calls.

Run directly to execute the grounded-generation test suite + grounding report:
    .venv/bin/python query.py
"""

from __future__ import annotations

from generation import FALLBACK_MESSAGE, generate
from retrieval import RELEVANCE_THRESHOLD, retrieve


def ask(question: str, k: int = 5) -> dict:
    """
    Full RAG pipeline: retrieve then generate.
    Returns {"answer": str, "sources": list[str], "chunks_used": int}

    Grounding guard: if no retrieved chunk is below RELEVANCE_THRESHOLD cosine
    distance, the question is out of scope for our documents, so we return the
    fallback message directly WITHOUT calling the LLM — we don't rely on the
    model alone to self-censor.
    """
    chunks = retrieve(question, k=k)

    relevant = [c for c in chunks if c["distance"] < RELEVANCE_THRESHOLD]
    if not relevant:
        return {"answer": FALLBACK_MESSAGE, "sources": [], "chunks_used": 0}

    # Pass the full retrieved set as context; relevance gate already passed.
    return generate(question, chunks)


# --- Grounded-generation test suite ------------------------------------------
# In-scope queries drawn from the Evaluation Plan in planning.md.
IN_SCOPE_QUERIES = [
    "What physical trait is shared by all Papas from the Emeritus bloodline?",
    "What does Vessel waking up in a hospital in the song Atlantic signify?",
    "What is the etiquette for a metal fan who wants to be near the stage but "
    "avoid moshing?",
]

# A question our documents (Ghost / Sleep Token / Rob Zombie lore + pit
# etiquette) clearly do NOT cover -> must trigger the fallback.
OUT_OF_SCOPE_QUERY = "What is Taylor Swift's concert ticket cancellation policy?"


def _print_result(query: str, result: dict) -> None:
    bar = "═" * 60
    print(bar)
    print(f'Query: "{query}"\n')
    print("Answer:")
    print(result["answer"], "\n")
    print("Sources used:", ", ".join(result["sources"]) if result["sources"] else "(none)")
    print("Chunks retrieved:", result["chunks_used"])
    print(bar + "\n")


def _run_tests() -> None:
    rows = []

    for query in IN_SCOPE_QUERIES:
        result = ask(query)
        _print_result(query, result)
        grounded = (result["answer"] != FALLBACK_MESSAGE) and result["chunks_used"] > 0
        cited = len(result["sources"]) > 0
        rows.append((query, "✅" if grounded else "❌", "✅" if cited else "❌", "N/A"))

    # Out-of-scope: expect the fallback message.
    result = ask(OUT_OF_SCOPE_QUERY)
    _print_result(OUT_OF_SCOPE_QUERY, result)
    fallback_ok = result["answer"] == FALLBACK_MESSAGE
    rows.append((OUT_OF_SCOPE_QUERY, "N/A", "N/A", "✅" if fallback_ok else "❌"))

    # --- Grounding report ---
    print("GROUNDING REPORT")
    print(f"{'Test':<5}{'Grounded?':<11}{'Sources cited?':<16}{'Fallback triggered?'}")
    for i, (_q, grounded, cited, fb) in enumerate(rows, start=1):
        label = f"{i} (oos)" if i == len(rows) else str(i)
        print(f"{label:<5}{grounded:<11}{cited:<16}{fb}")
    print("\nQueries (in order):")
    for i, (q, *_rest) in enumerate(rows, start=1):
        print(f"  {i}. {q}")


if __name__ == "__main__":
    _run_tests()
