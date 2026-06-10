"""
Milestone 5 — Gradio interface
The Unofficial Guide to Band Lore and Concert Culture

A minimal web UI over the RAG pipeline. Type a question about Ghost, Sleep
Token, or Rob Zombie lore / concert culture and get a grounded answer plus the
source documents it was drawn from.

Run:
    .venv/bin/python app.py
Then open http://localhost:7860
"""

from __future__ import annotations

import gradio as gr

from query import ask


def handle_query(question: str) -> tuple[str, str]:
    """Gradio callback: run a question through the RAG pipeline.

    Returns (answer, sources) as two strings for the two output textboxes.
    """
    if not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"]) or "(no sources)"
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide to Band Lore") as demo:
    gr.Markdown(
        "# The Unofficial Guide to Band Lore and Concert Culture\n"
        "Ask about **Ghost**, **Sleep Token**, or **Rob Zombie** lore, setlists, "
        "and pit etiquette. Answers are grounded only in the collected fan threads."
    )
    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. What do all the Papas from the Emeritus bloodline have in common?",
    )
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    # Both the button and pressing Enter in the textbox submit the question.
    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    # share=True also creates a temporary public link (~72h) for demos/recording;
    # the app still serves locally at http://localhost:7860 exactly as before.
    demo.launch(share=True)
