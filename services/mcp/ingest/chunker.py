"""Structure-aware chunking: split on document sections, then ~512-token windows w/ overlap."""
from __future__ import annotations

from dataclasses import dataclass

TARGET_TOKENS = 512
OVERLAP = 0.12


@dataclass
class Chunk:
    section: str
    ordinal: int
    text: str
    token_count: int


def chunk_document(text: str, sections: list[tuple[str, str]] | None = None) -> list[Chunk]:
    """TODO(Phase 1): detect sections (headings), then window each section into
    ~TARGET_TOKENS chunks with OVERLAP. Write the unit test FIRST (TDD)."""
    raise NotImplementedError("Implement in Phase 1 with a unit test first.")
