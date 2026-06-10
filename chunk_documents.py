"""
Milestone 3 — Ingestion and chunking
The Unofficial Guide to Band Lore and Concert Culture

Reads every .txt file in the documents/ folder (doc1.txt ... doc10.txt),
cleans out boilerplate / markdown / UI noise, and splits the substantive
text into chunks using the planning.md spec:
    chunk size = 800 characters, overlap = 150 characters.

Each chunk keeps its source filename as metadata so the embedding step
(Milestone 4) can attribute retrieved chunks back to a document.

Run:
    python chunk_documents.py
"""

import html
import random
import re
from dataclasses import dataclass
from pathlib import Path

# --- Configuration (matches planning.md "Chunking Strategy") -----------------
DOCUMENTS_DIR = Path(__file__).parent / "documents"
CHUNK_SIZE = 900        # characters per chunk
CHUNK_OVERLAP = 175     # characters shared between consecutive chunks

# Lines that start with one of these labels are metadata/UI noise, not content,
# so the whole line is dropped. Matched case-insensitively at the line start.
BOILERPLATE_LABELS = (
    "title",
    "thread title",
    "author",
    "subreddit",
    "initial post",
    "comments",
    "comments section",
    "edit",
    "eta",
)

# A Reddit comment-author header that sits on its own line, e.g.
#   "EnigmaEnthusiast17:"  "[deleted]:"  "bigsigh7 [OP] (2y ago):"  "Farmer33 (OP):"
# These repeat before every comment and carry no domain content, so the whole
# line is dropped. The pattern requires the line to END at the colon, so real
# sentences with a mid-line colon (e.g. "Papa Emeritus: The character...") stay.
COMMENT_HEADER_RE = re.compile(
    r"^\s*\[?[A-Za-z0-9][\w\-./]*\]?"        # username token (optionally [bracketed])
    r"(?:\s*[\[(]OP[\])])?"                  # optional [OP] / (OP)
    r"(?:\s*\(\s*\d+\s*[a-z]+\s+ago\s*\))?"  # optional "(2y ago)" timestamp
    r"(?:\s*[\[(]OP[\])])?"                  # optional OP after the timestamp
    r"\s*:\s*$",                             # ...ending right at the colon
    re.IGNORECASE,
)


@dataclass
class Chunk:
    """A single chunk of text plus the metadata Milestone 4 will need."""
    source: str        # source filename, e.g. "doc1.txt"
    chunk_index: int   # position of this chunk within its document
    text: str


# --- Cleaning ----------------------------------------------------------------
def _is_boilerplate_line(line: str) -> bool:
    """True if the line is a metadata label, a decorative rule, or empty noise."""
    stripped = line.strip()
    if not stripped:
        return False  # blank lines are handled by whitespace collapsing later

    # Decorative separators like "--------" or "======".
    if re.fullmatch(r"[-=_*~]{3,}", stripped):
        return True

    # A standalone "COMMENTS SECTION" style banner (no colon).
    if stripped.lower() in BOILERPLATE_LABELS:
        return True

    # Labeled metadata lines: "Author: ...", "Subreddit: ...", "Title: ...".
    label = stripped.split(":", 1)[0].strip().lower()
    if ":" in stripped and label in BOILERPLATE_LABELS:
        return True

    return False


def _looks_like_title(line: str) -> bool:
    """Heuristic for an untagged title line (e.g. doc1's ALL-CAPS heading)."""
    stripped = line.strip()
    if not stripped:
        return False
    letters = [c for c in stripped if c.isalpha()]
    # All-caps heading with no sentence-ending punctuation.
    if letters and stripped == stripped.upper() and not stripped.endswith((".", "!", "?")):
        return True
    # "Some thread title : r/SubredditName" style.
    if re.search(r":\s*r/\w+\s*$", stripped):
        return True
    return False


def clean_text(raw: str) -> str:
    """Strip boilerplate/markdown/HTML/UI noise and return substantive text.

    Paragraph structure is preserved: each surviving line (a Reddit comment or
    a lore paragraph) becomes one newline-separated paragraph, so the
    paragraph-aware chunker can pack whole paragraphs together. Whitespace is
    only collapsed *within* a paragraph, never across the line breaks between
    paragraphs.
    """
    text = html.unescape(raw)                       # &amp;, &nbsp; -> & , space
    text = re.sub(r"<[^>]+>", " ", text)            # drop HTML tags
    text = re.sub(r"\[([^\]]+)\]\((?:[^)]+)\)", r"\1", text)  # [label](url) -> label
    text = re.sub(r"https?://\S+", "", text)        # bare URLs

    lines = text.splitlines()

    # Drop a leading untagged title line if present (only the first content line).
    for idx, line in enumerate(lines):
        if line.strip():
            if _looks_like_title(line):
                lines[idx] = ""
            break

    paragraphs: list[str] = []
    for ln in lines:
        # Drop metadata labels, decorative rules, and per-comment author headers.
        if _is_boilerplate_line(ln) or COMMENT_HEADER_RE.match(ln):
            continue
        ln = re.sub(r"\[(?:deleted|removed)\]", "", ln, flags=re.IGNORECASE)
        ln = re.sub(r"[*_`~#>]+", "", ln)           # markdown emphasis/heading/quote
        ln = re.sub(r"^\s*[-+]\s+", "", ln)         # list bullets
        ln = re.sub(r"\s+", " ", ln).strip()        # collapse whitespace within line
        if ln:
            paragraphs.append(ln)

    # One newline per paragraph -> the chunker splits on these boundaries.
    return "\n".join(paragraphs)


# --- Chunking ----------------------------------------------------------------
def _split_on_words(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Fallback splitter for a single paragraph longer than `chunk_size`.

    Cuts on word boundaries (the last space at or before the size limit) and
    overlaps the next piece by ~`overlap` characters, so no word is split.
    """
    chunks: list[str] = []
    n = len(text)
    start = 0
    while start < n:
        end = start + chunk_size
        if end >= n:
            piece = text[start:].strip()
            if piece:
                chunks.append(piece)
            break
        break_at = text.rfind(" ", start, end)
        if break_at <= start:              # no space in window (very long token)
            break_at = end                 # fall back to a hard cut
        piece = text[start:break_at].strip()
        if piece:
            chunks.append(piece)
        next_start = break_at - overlap
        if next_start <= start:
            next_start = break_at
        else:
            space = text.rfind(" ", start, next_start)
            if space != -1:
                next_start = space + 1
        start = next_start
    return chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Paragraph-aware chunking with paragraph-level overlap.

    `clean_text` emits one paragraph per line. We greedily pack consecutive
    whole paragraphs into a chunk until adding the next would exceed
    `chunk_size`, so chunks start and end on paragraph boundaries (whole
    Reddit comments / lore paragraphs) instead of mid-sentence. When a chunk
    is closed, we step back over the trailing paragraph(s) that fit within
    ~`overlap` characters and repeat them at the start of the next chunk, so
    context carries across the seam. A single paragraph longer than
    `chunk_size` is split on word boundaries via `_split_on_words`.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    # Build the list of units: whole paragraphs, with oversized ones pre-split.
    units: list[str] = []
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            continue
        if len(para) > chunk_size:
            units.extend(_split_on_words(para, chunk_size, overlap))
        else:
            units.append(para)

    if not units:
        return []

    chunks: list[str] = []
    i = 0
    n = len(units)
    while i < n:
        # Pack paragraphs starting at i until the next one wouldn't fit.
        cur_len = 0
        j = i
        while j < n:
            extra = len(units[j]) + (1 if j > i else 0)  # +1 for joining space
            if j > i and cur_len + extra > chunk_size:
                break
            cur_len += extra
            j += 1
        chunks.append(" ".join(units[i:j]))

        if j >= n:
            break

        # Overlap: step back over trailing paragraphs that fit within `overlap`.
        back_len = 0
        overlap_units = 0
        k = j - 1
        while k > i:  # k > i guarantees at least one new paragraph next round
            seg = len(units[k]) + (1 if overlap_units else 0)
            if back_len + seg > overlap:
                break
            back_len += seg
            overlap_units += 1
            k -= 1
        i = j - overlap_units if (j - overlap_units) > i else i + 1

    return chunks


# --- Ingestion ---------------------------------------------------------------
def load_and_chunk(documents_dir: Path = DOCUMENTS_DIR) -> list[Chunk]:
    """Load every .txt file, clean it, chunk it, and tag chunks with their source."""
    if not documents_dir.exists():
        raise FileNotFoundError(f"Documents directory not found: {documents_dir}")

    txt_files = sorted(
        documents_dir.glob("*.txt"),
        key=lambda p: int(m.group()) if (m := re.search(r"\d+", p.stem)) else 0,
    )
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in {documents_dir}")

    all_chunks: list[Chunk] = []
    for path in txt_files:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        cleaned = clean_text(raw)
        doc_chunks = [
            Chunk(source=path.name, chunk_index=i, text=t)
            for i, t in enumerate(chunk_text(cleaned))
        ]
        all_chunks.extend(doc_chunks)
        print(f"  {path.name}: {len(raw):>6} raw -> {len(cleaned):>6} cleaned "
              f"chars -> {len(doc_chunks)} chunks")

    return all_chunks


# --- Verification ------------------------------------------------------------
def main() -> None:
    print(f"Loading documents from: {DOCUMENTS_DIR}\n")
    chunks = load_and_chunk()

    print(f"\nTotal chunks across all documents: {len(chunks)}")
    longest = max(len(c.text) for c in chunks)
    print(f"Longest chunk: {longest} characters (limit {CHUNK_SIZE})")
    assert longest <= CHUNK_SIZE, "A chunk exceeded the configured chunk size!"

    print("\n--- 5 random chunks for manual verification ---")
    for c in random.sample(chunks, k=min(5, len(chunks))):
        print(f"\n[{c.source} #{c.chunk_index}] ({len(c.text)} chars)")
        print(c.text)


if __name__ == "__main__":
    main()
