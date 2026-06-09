"""Ingest the local corpus folder into the DB.  Usage: python -m ingest.seed data/"""
from __future__ import annotations

import sys


def main(folder: str) -> None:
    """TODO(Phase 1): for each file -> load text -> chunk_document() -> embed_passages()
    -> INSERT documents + chunks. Keep it idempotent. Test against a tiny fixture first."""
    raise NotImplementedError("Phase 1: load, chunk, embed, insert.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/")
