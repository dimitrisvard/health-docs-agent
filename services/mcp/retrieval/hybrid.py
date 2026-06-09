"""Hybrid retrieval: dense (pgvector cosine) + lexical (Postgres FTS) fused with RRF."""
from __future__ import annotations

import os

import psycopg
from pgvector.psycopg import register_vector

from ingest.embedder import embed_query
from retrieval.fusion import reciprocal_rank_fusion

DB = os.environ["DATABASE_URL"]
POOL = 20  # candidates per arm before fusion


def _vec_literal(vec) -> str:
    """pgvector text literal so the query embedding binds as `vector`, not float8[]."""
    return "[" + ",".join(repr(float(x)) for x in vec) + "]"


def _conn():
    conn = psycopg.connect(DB, autocommit=True)
    register_vector(conn)
    return conn


def _dense_ids(cur, qvec, kind, document_id) -> list[str]:
    clauses, params = [], []
    if kind:
        clauses.append("d.kind = %s")
        params.append(kind)
    if document_id:
        clauses.append("c.document_id = %s")
        params.append(document_id)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    cur.execute(
        f"SELECT c.id FROM chunks c JOIN documents d ON d.id = c.document_id"
        f"{where} ORDER BY c.embedding <=> %s::vector LIMIT %s",
        (*params, _vec_literal(qvec), POOL),
    )
    return [str(r[0]) for r in cur.fetchall()]


def _lexical_ids(cur, query, kind, document_id) -> list[str]:
    clauses = ["c.ts @@ websearch_to_tsquery('english', %s)"]
    params: list = [query]
    if kind:
        clauses.append("d.kind = %s")
        params.append(kind)
    if document_id:
        clauses.append("c.document_id = %s")
        params.append(document_id)
    where = " WHERE " + " AND ".join(clauses)
    cur.execute(
        f"SELECT c.id FROM chunks c JOIN documents d ON d.id = c.document_id{where} "
        f"ORDER BY ts_rank(c.ts, websearch_to_tsquery('english', %s)) DESC LIMIT %s",
        (*params, query, POOL),
    )
    return [str(r[0]) for r in cur.fetchall()]


def _hydrate(cur, ids: list[int]) -> list[dict]:
    if not ids:
        return []
    cur.execute(
        "SELECT c.id, c.document_id, c.section, c.text, d.title, d.source_uri "
        "FROM chunks c JOIN documents d ON d.id = c.document_id WHERE c.id = ANY(%s)",
        (ids,),
    )
    cols = ["id", "document_id", "section", "text", "title", "source_uri"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def hybrid_search(query: str, k: int = 5, kind: str | None = None,
                  document_id: int | None = None) -> list[dict]:
    qvec = embed_query(query)
    with _conn() as conn, conn.cursor() as cur:
        dense = _dense_ids(cur, qvec, kind, document_id)
        lexical = _lexical_ids(cur, query, kind, document_id)
        fused = reciprocal_rank_fusion([dense, lexical])
        top = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:k]
        rows = _hydrate(cur, [int(i) for i, _ in top])
    for r in rows:
        r["score"] = fused[str(r["id"])]
    return sorted(rows, key=lambda r: r["score"], reverse=True)


def fetch_section(document_id: int, section: str) -> list[dict]:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, ordinal, text FROM chunks WHERE document_id = %s AND section = %s ORDER BY ordinal",
            (document_id, section),
        )
        return [{"id": r[0], "ordinal": r[1], "text": r[2]} for r in cur.fetchall()]


def list_sources() -> list[dict]:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, kind, title, source_uri FROM documents ORDER BY id")
        return [{"id": r[0], "kind": r[1], "title": r[2], "source_uri": r[3]} for r in cur.fetchall()]
