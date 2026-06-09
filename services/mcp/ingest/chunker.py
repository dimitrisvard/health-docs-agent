"""Structure-aware chunking: split on document sections, then ~512-token windows w/ overlap.

Token counts are a deterministic whitespace-word approximation — no tokenizer dependency
is pulled in just to chunk. bge truncates at its own max length if a window runs long.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

TARGET_TOKENS = 512
OVERLAP = 0.12
DEFAULT_SECTION = "Body"

# Heading forms we recognise in clinical-style docs:
#   - Markdown ATX:        "## Contraindications"
#   - Numbered:            "4.3 Contraindications" / "1. Introduction"
#   - ALL-CAPS title line: "DOSAGE AND ADMINISTRATION"
_MD = re.compile(r"^#{1,6}\s+(.+?)\s*#*$")
_NUM = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$")
_MAX_HEADING_LEN = 80


@dataclass
class Chunk:
    section: str
    ordinal: int
    text: str
    token_count: int


def _heading(line: str) -> str | None:
    """Return the heading label for a line, or None if it is body text."""
    s = line.strip()
    if not s:
        return None
    md = _MD.match(s)
    if md:
        return md.group(1).strip()
    if any(c.isalpha() for c in s) and s == s.upper() and len(s) <= _MAX_HEADING_LEN and not s.endswith("."):
        return s
    num = _NUM.match(s)
    if num:
        rest = num.group(2).strip()
        if rest and rest[0].isupper() and len(s) <= _MAX_HEADING_LEN and not s.endswith("."):
            return s
    return None


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split raw text into (section_label, section_body) pairs by detected headings.

    Text before the first heading is retained under DEFAULT_SECTION.
    """
    sections: list[tuple[str, str]] = []
    name = DEFAULT_SECTION
    body: list[str] = []
    for line in text.splitlines():
        heading = _heading(line)
        if heading is not None:
            joined = "\n".join(body).strip()
            if joined:
                sections.append((name, joined))
            name, body = heading, []
        else:
            body.append(line)
    joined = "\n".join(body).strip()
    if joined:
        sections.append((name, joined))
    return sections


def _window(body: str) -> list[str]:
    """Slide a ~TARGET_TOKENS word window over a section body with OVERLAP carry-over."""
    words = body.split()
    if not words:
        return []
    if len(words) <= TARGET_TOKENS:
        return [body.strip()]
    overlap = max(1, round(TARGET_TOKENS * OVERLAP))
    step = TARGET_TOKENS - overlap
    windows: list[str] = []
    i = 0
    while i < len(words):
        windows.append(" ".join(words[i : i + TARGET_TOKENS]))
        if i + TARGET_TOKENS >= len(words):
            break
        i += step
    return windows


def chunk_document(text: str, sections: list[tuple[str, str]] | None = None) -> list[Chunk]:
    """Detect sections (unless given), window each, and return ordered Chunks.

    Ordinals are document-wide and 0-based, preserving reading order.
    """
    secs = sections if sections is not None else split_sections(text)
    chunks: list[Chunk] = []
    ordinal = 0
    for name, body in secs:
        for window in _window(body):
            chunks.append(Chunk(section=name, ordinal=ordinal, text=window, token_count=len(window.split())))
            ordinal += 1
    return chunks
