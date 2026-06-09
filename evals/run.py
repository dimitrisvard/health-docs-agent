"""Run the golden set: retrieval metrics + faithfulness, write results to the DB.
Usage (inside the agent container, repo mounted):  python -m evals.run
"""
from __future__ import annotations

import json
import pathlib

from evals.metrics import hit_at_k, mrr, ndcg  # noqa: F401  (used in Phase 5)

DATASET = pathlib.Path(__file__).parent / "dataset" / "sample.jsonl"
K = 5
THRESHOLDS = {"hit_at_5": 0.7, "faithfulness": 0.8}


def load() -> list[dict]:
    return [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]


def main() -> int:
    cases = load()
    # TODO(Phase 5):
    #  1. for each case -> call MCP hybrid_search, collect retrieved chunk ids
    #  2. compute hit@k / mrr / ndcg vs case["relevant_chunk_ids"]
    #  3. call the agent -> judge faithfulness with an LLM-as-judge prompt
    #  4. write eval_runs + eval_results rows; print a table
    #  5. return non-zero if any THRESHOLD is missed (so CI fails)
    raise NotImplementedError(f"Wire to MCP + agent in Phase 5. Loaded {len(cases)} cases.")


if __name__ == "__main__":
    raise SystemExit(main())
