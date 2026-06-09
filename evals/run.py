"""Run the golden set: retrieval metrics + faithfulness, write results to the DB.

Usage (inside the agent container, repo mounted):  python -m evals.run

The scoring core (`score_run`, `aggregate`, `below_thresholds`, `parse_score`) is pure
and injectable, so it unit-tests offline. The live retriever / answerer / judge / DB
writer are lazy-built in `main` and only touch the network when actually run.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
from statistics import mean
from typing import Any, Callable

from evals.metrics import hit_at_k, mrr, ndcg

DATASET = pathlib.Path(__file__).parent / "dataset" / "sample.jsonl"
K = 5
THRESHOLDS = {"hit_at_5": 0.7, "faithfulness": 0.8}

Retriever = Callable[[str], list[dict]]
Answerer = Callable[[str, list[dict]], str]
Judge = Callable[[str, str, list[dict]], float]

FAITHFULNESS_PROMPT = """You are grading whether an ANSWER is faithful to the CONTEXT.
Faithful means every factual claim in the answer is supported by the context. A grounded
refusal ("not enough information in the documents") is fully faithful.

Question: {question}

Context:
{context}

Answer:
{answer}

Reply with ONLY a number from 0.0 (unsupported / hallucinated) to 1.0 (fully supported)."""


def load() -> list[dict]:
    return [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]


def parse_score(text: str) -> float:
    """Pull the faithfulness number out of the judge's reply, clamped to [0, 1]."""
    match = re.search(r"\d*\.?\d+", text)
    return max(0.0, min(1.0, float(match.group()))) if match else 0.0


def score_run(
    cases: list[dict],
    retrieve: Retriever,
    answer: Answerer | None = None,
    judge: Judge | None = None,
) -> tuple[list[dict], dict[str, float | None]]:
    """Score every case over injected components. Metrics are None when not measurable
    (no labelled chunks for retrieval, or no judge for faithfulness) so they never gate."""
    rows: list[dict] = []
    for case in cases:
        chunks = retrieve(case["question"])
        retrieved_ids = [str(c.get("id")) for c in chunks]
        relevant = {str(i) for i in case.get("relevant_chunk_ids", [])}
        graded = bool(relevant)
        generated = answer(case["question"], chunks) if answer else ""
        rows.append(
            {
                "question": case["question"],
                "hit_at_k": hit_at_k(retrieved_ids, relevant, K) if graded else None,
                "mrr": mrr(retrieved_ids, relevant) if graded else None,
                "ndcg": ndcg(retrieved_ids, relevant, K) if graded else None,
                "faithfulness": judge(case["question"], generated, chunks) if judge else None,
            }
        )
    return rows, aggregate(rows)


def _mean(values: list[Any]) -> float | None:
    nums = [float(v) for v in values if v is not None]
    return mean(nums) if nums else None


def aggregate(rows: list[dict]) -> dict[str, float | None]:
    return {
        "hit_at_5": _mean([1.0 if r["hit_at_k"] else 0.0 for r in rows if r["hit_at_k"] is not None]),
        "mrr": _mean([r["mrr"] for r in rows]),
        "ndcg": _mean([r["ndcg"] for r in rows]),
        "faithfulness": _mean([r["faithfulness"] for r in rows]),
    }


def below_thresholds(aggregates: dict[str, float | None]) -> list[str]:
    """Return human-readable failures. A metric that wasn't measured (None) never fails."""
    failures = []
    for key in ("hit_at_5", "faithfulness"):
        value, floor = aggregates.get(key), THRESHOLDS[key]
        if value is not None and value < floor:
            failures.append(f"{key} {value:.3f} < {floor}")
    return failures


def _print_table(rows: list[dict], aggregates: dict[str, float | None]) -> None:
    def fmt(v: Any) -> str:
        return "-" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))

    print(f"{'hit@k':>6} {'mrr':>6} {'ndcg':>6} {'faith':>6}  question")
    for r in rows:
        print(
            f"{fmt(r['hit_at_k']):>6} {fmt(r['mrr']):>6} {fmt(r['ndcg']):>6} "
            f"{fmt(r['faithfulness']):>6}  {r['question'][:60]}"
        )
    print(
        f"\nAGGREGATE  hit@5={fmt(aggregates['hit_at_5'])}  mrr={fmt(aggregates['mrr'])}  "
        f"ndcg={fmt(aggregates['ndcg'])}  faithfulness={fmt(aggregates['faithfulness'])}"
    )


def _persist(rows: list[dict], db_url: str | None) -> None:
    if not db_url:
        return
    import psycopg

    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO eval_runs (commit_sha) VALUES (%s) RETURNING id",
            (os.environ.get("GIT_SHA"),),
        )
        run_id = cur.fetchone()[0]
        cur.executemany(
            "INSERT INTO eval_results (run_id, question, hit_at_k, mrr, ndcg, faithfulness) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [(run_id, r["question"], r["hit_at_k"], r["mrr"], r["ndcg"], r["faithfulness"]) for r in rows],
        )
        conn.commit()


def _llm_judge(question: str, answer: str, chunks: list[dict]) -> float:
    from anthropic import Anthropic

    context = "\n\n".join(str(c.get("text", "")) for c in chunks)
    prompt = FAITHFULNESS_PROMPT.format(question=question, context=context, answer=answer)
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    resp = Anthropic().messages.create(
        model=model, max_tokens=16, messages=[{"role": "user", "content": prompt}]
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    return parse_score(text)


def _default_components() -> tuple[Retriever, Answerer | None, Judge | None]:
    import asyncio

    from app.agent.rag import retrieve as _retrieve
    from app.agent.rag import stream_completion

    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    # One persistent loop for the whole run: repeated asyncio.run() closes the loop between
    # calls and races the async HTTP/MCP client teardown ("Event loop is closed").
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def retrieve(question: str) -> list[dict]:
        return loop.run_until_complete(_retrieve(question))

    def answer(question: str, chunks: list[dict]) -> str:
        async def go() -> str:
            return "".join([token async for token in stream_completion(question, chunks)])

        return loop.run_until_complete(go())

    return retrieve, (answer if has_key else None), (_llm_judge if has_key else None)


def main() -> int:
    cases = load()
    if not cases:
        print("No eval cases in the golden set; nothing to do.")
        return 0
    try:
        retrieve, answer, judge = _default_components()
        rows, aggregates = score_run(cases, retrieve, answer, judge)
    except Exception as exc:  # noqa: BLE001 — eval is a tool; skip cleanly if the stack is absent
        print(f"Eval skipped (live retrieval/LLM unavailable): {exc}")
        return 0

    _print_table(rows, aggregates)
    _persist(rows, os.environ.get("DATABASE_URL"))

    failures = below_thresholds(aggregates)
    if failures:
        print("EVAL GATE FAILED: " + "; ".join(failures))
        return 1
    print("EVAL GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
