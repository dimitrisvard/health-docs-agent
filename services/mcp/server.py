"""FastMCP retrieval server.

Exposes hybrid search + helpers as MCP tools. The SAME server is consumed by the
agent (services/agent) over HTTP *and* by Claude Code/Desktop via .mcp.json.
Run standalone:  python server.py   (serves Streamable HTTP at /mcp on :8000)
"""
from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from retrieval.hybrid import (
    hybrid_search as _hybrid_search,
    fetch_section as _fetch_section,
    list_sources as _list_sources,
)

mcp = FastMCP("retrieval")


@mcp.tool
def hybrid_search(
    query: Annotated[str, Field(description="Natural-language question to search the corpus for")],
    k: Annotated[int, Field(description="Number of fused results to return")] = 5,
    kind: Annotated[str | None, Field(description="Filter: 'trial' | 'drug_label' | 'guideline'")] = None,
) -> list[dict]:
    """Hybrid (dense + lexical) search over the corpus, fused with Reciprocal Rank Fusion.
    Returns chunks with text, source title, section, and fusion score."""
    return _hybrid_search(query=query, k=k, kind=kind)


@mcp.tool
def fetch_section(
    document_id: Annotated[int, Field(description="Document id from list_sources / search results")],
    section: Annotated[str, Field(description="Section name, e.g. 'Contraindications'")],
) -> list[dict]:
    """Return all chunks of a named section within a document, in order."""
    return _fetch_section(document_id=document_id, section=section)


@mcp.tool
def compare_documents(
    query: Annotated[str, Field(description="What to compare across the documents")],
    document_ids: Annotated[list[int], Field(description="Document ids to compare")],
    k: Annotated[int, Field(description="Results per document")] = 4,
) -> dict[int, list[dict]]:
    """Run hybrid search scoped to each document so the agent can compare them side by side."""
    return {doc_id: _hybrid_search(query=query, k=k, document_id=doc_id) for doc_id in document_ids}


@mcp.tool
def list_sources() -> list[dict]:
    """List ingested documents (id, kind, title, source_uri) so the agent knows what exists."""
    return _list_sources()


@mcp.tool
def ingest_document(
    filename: Annotated[str, Field(description="Original file name; kind + title are derived from it")],
    text: Annotated[str, Field(description="Already-extracted document text to chunk, embed, and store")],
) -> dict:
    """Chunk, embed, and store a document (idempotent by title). Returns {document_id, title, kind, chunks}.

    Ingestion lives here, not in the agent. Not in the agent's allowed_tools — the LLM
    cannot ingest; only the upload endpoint calls this directly over the MCP client.
    """
    import os

    import psycopg
    from pgvector.psycopg import register_vector

    from ingest.seed import ensure_schema, infer_kind, ingest_text, title_from

    title, kind = title_from(filename), infer_kind(filename)
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        register_vector(conn)
        ensure_schema(conn)
        document_id, chunks = ingest_text(conn, title, kind, text)
    return {"document_id": document_id, "title": title, "kind": kind, "chunks": chunks}


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
