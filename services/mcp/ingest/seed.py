"""Ingest the local corpus folder into the DB.  Usage: python -m ingest.seed data/

Idempotent: re-seeding replaces a document (matched by title) and its chunks, so the
DB always reflects the current files. Logs ids/counts only — never document bodies.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

import structlog

from ingest.chunker import chunk_document

log = structlog.get_logger()

TEXT_SUFFIXES = {".txt", ".md", ".markdown"}
PDF_SUFFIXES = {".pdf"}
SUPPORTED = TEXT_SUFFIXES | PDF_SUFFIXES
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "db" / "schema.sql"

Embedder = Callable[[list[str]], list[list[float]]]


def infer_kind(filename: str) -> str:
    """Map a filename to a corpus kind for filtering and citations."""
    name = filename.lower()
    if any(t in name for t in ("trial", "protocol", "nct")):
        return "trial"
    if any(t in name for t in ("label", "smpc", "spc", "pil", "prescribing")):
        return "drug_label"
    return "guideline"


def title_from(filename: str) -> str:
    return Path(filename).stem.replace("_", " ").replace("-", " ").strip()


def _load_pdf(path: Path) -> str:
    from pypdf import PdfReader  # lazy: only PDF corpora need it

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8")
    if suffix in PDF_SUFFIXES:
        return _load_pdf(path)
    raise ValueError(f"Unsupported file type: {path.name}")


def discover(folder: str | Path) -> list[Path]:
    """List ingestible corpus files (README and unsupported types excluded)."""
    root = Path(folder)
    return sorted(
        p
        for p in root.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED and p.stem.lower() != "readme"
    )


def _vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in vec) + "]"


def ingest_text(
    conn: Any, title: str, kind: str, text: str, embed: Embedder | None = None
) -> tuple[int, int]:
    """Replace any same-titled document, then insert its chunks + embeddings.

    Returns (document_id, n_chunks). `embed` is injectable for testing. This is the
    shared core used by both the seed CLI and the MCP ingest_document tool.
    """
    if embed is None:
        from ingest.embedder import embed_passages  # lazy: avoids loading the model at import

        embed = embed_passages

    chunks = chunk_document(text)

    with conn.cursor() as cur:
        cur.execute("DELETE FROM documents WHERE title = %s", (title,))
        cur.execute(
            "INSERT INTO documents (kind, title, source_uri) VALUES (%s, %s, %s) RETURNING id",
            (kind, title, None),
        )
        document_id = cur.fetchone()[0]
        if chunks:
            vectors = embed([c.text for c in chunks])
            cur.executemany(
                "INSERT INTO chunks (document_id, section, ordinal, text, token_count, embedding) "
                "VALUES (%s, %s, %s, %s, %s, %s::vector)",
                [
                    (document_id, c.section, c.ordinal, c.text, c.token_count, _vector_literal(vec))
                    for c, vec in zip(chunks, vectors)
                ],
            )
    conn.commit()
    log.info("ingested", title=title, kind=kind, chunks=len(chunks))
    return document_id, len(chunks)


def ingest_file(conn: Any, path: Path, embed: Embedder | None = None) -> int:
    """Ingest a corpus file: derive title/kind from the name, then store it."""
    _, n = ingest_text(conn, title_from(path.name), infer_kind(path.name), load_text(path), embed=embed)
    return n


def ensure_schema(conn: Any) -> None:
    """Apply the committed schema (idempotent) so seed works on a bare DB too."""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def main(folder: str) -> None:
    import os

    import psycopg
    from pgvector.psycopg import register_vector

    files = discover(folder)
    if not files:
        log.warning("no_supported_files", folder=str(folder))
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        register_vector(conn)
        ensure_schema(conn)
        total = sum(ingest_file(conn, p) for p in files)
    log.info("seed_complete", documents=len(files), chunks=total)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/")
