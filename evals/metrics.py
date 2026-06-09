"""Retrieval metrics. Pure functions, fully unit-testable."""
from __future__ import annotations

import math


def hit_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> bool:
    return any(i in relevant_ids for i in retrieved_ids[:k])


def mrr(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for rank, i in enumerate(retrieved_ids, start=1):
        if i in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, i in enumerate(retrieved_ids[:k], start=1)
        if i in relevant_ids
    )
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(len(relevant_ids), k) + 1))
    return (dcg / ideal) if ideal else 0.0
