from evals.run import aggregate, below_thresholds, parse_score, score_run

CASES = [
    {"question": "exclusion criteria?", "relevant_chunk_ids": [2]},
    {"question": "contraindications?", "relevant_chunk_ids": [9]},  # will be missed
]


def _retriever(question: str) -> list[dict]:
    # chunk 2 is rank 1 for the first case; nothing relevant for the second
    return [{"id": 2, "text": "eligibility"}, {"id": 5, "text": "other"}]


def test_score_run_computes_retrieval_and_faithfulness():
    rows, agg = score_run(
        CASES,
        retrieve=_retriever,
        answer=lambda q, chunks: "grounded answer",
        judge=lambda q, a, chunks: 0.9,
    )
    assert rows[0]["hit_at_k"] is True and rows[0]["mrr"] == 1.0
    assert rows[1]["hit_at_k"] is False  # chunk 9 never retrieved
    assert agg["hit_at_5"] == 0.5  # one hit out of two
    assert agg["faithfulness"] == 0.9


def test_metrics_are_none_without_labels_or_judge():
    rows, agg = score_run(
        [{"question": "unlabelled", "relevant_chunk_ids": []}],
        retrieve=_retriever,
    )
    assert rows[0]["hit_at_k"] is None and rows[0]["faithfulness"] is None
    assert agg["hit_at_5"] is None and agg["faithfulness"] is None


def test_below_thresholds_gates_only_measured_metrics():
    assert below_thresholds({"hit_at_5": 0.9, "faithfulness": 0.9}) == []
    assert below_thresholds({"hit_at_5": 0.5, "faithfulness": 0.9})  # hit@5 too low
    # unmeasured metrics (None) never fail the build
    assert below_thresholds({"hit_at_5": None, "faithfulness": None}) == []


def test_parse_score_clamps_and_extracts():
    assert parse_score("0.9") == 0.9
    assert parse_score("Score: 1.0") == 1.0
    assert parse_score("2") == 1.0  # clamped
    assert parse_score("no number here") == 0.0


def test_aggregate_ignores_none():
    rows = [{"hit_at_k": True, "mrr": 1.0, "ndcg": 1.0, "faithfulness": None}]
    agg = aggregate(rows)
    assert agg["mrr"] == 1.0 and agg["faithfulness"] is None
