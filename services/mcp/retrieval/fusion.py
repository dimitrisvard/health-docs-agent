"""Reciprocal Rank Fusion (RRF)."""
from __future__ import annotations


def reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = 60) -> dict[str, float]:
    """Fuse ranked lists of ids into one score map.

    score(id) = sum over lists of 1 / (k + rank), with 0-based rank.
    Items appearing high in multiple lists win. k dampens the weight of deep ranks.
    """
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, item_id in enumerate(ranked):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
    return scores
