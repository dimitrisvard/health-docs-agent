"""Read the latest eval run from the DB for the /evals dashboard.

Aggregates are recomputed from the stored per-question rows (the schema keeps rows, not
summaries), so the dashboard and the CI gate read the same numbers.
"""
from __future__ import annotations

import os
from statistics import mean
from typing import Any


def _mean(values: list[Any]) -> float | None:
    nums = [float(v) for v in values if v is not None]
    return mean(nums) if nums else None


def _aggregate(results: list[dict]) -> dict[str, float | None]:
    return {
        "hit_at_5": _mean([1.0 if r["hit_at_k"] else 0.0 for r in results if r["hit_at_k"] is not None]),
        "mrr": _mean([r["mrr"] for r in results]),
        "ndcg": _mean([r["ndcg"] for r in results]),
        "faithfulness": _mean([r["faithfulness"] for r in results]),
    }


def latest_eval() -> dict[str, Any] | None:
    """Latest eval_run with its results + recomputed aggregates, or None if unavailable."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return None
    import psycopg

    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute("SELECT id, commit_sha, created_at FROM eval_runs ORDER BY id DESC LIMIT 1")
        run = cur.fetchone()
        if not run:
            return None
        cur.execute(
            "SELECT question, hit_at_k, mrr, ndcg, faithfulness FROM eval_results "
            "WHERE run_id = %s ORDER BY id",
            (run[0],),
        )
        rows = cur.fetchall()

    results = [
        {"question": r[0], "hit_at_k": r[1], "mrr": r[2], "ndcg": r[3], "faithfulness": r[4]}
        for r in rows
    ]
    return {
        "run": {
            "id": run[0],
            "commit_sha": run[1],
            "created_at": run[2].isoformat() if run[2] else None,
        },
        "aggregates": _aggregate(results),
        "results": results,
    }
