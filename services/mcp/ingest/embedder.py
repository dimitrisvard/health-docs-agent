"""Local embeddings via FastEmbed (bge-base-en-v1.5, 768d). No API key required."""
from __future__ import annotations

import os
from functools import lru_cache

from fastembed import TextEmbedding

MODEL = os.environ.get("EMBED_MODEL", "BAAI/bge-base-en-v1.5")


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(model_name=MODEL)


def embed_query(text: str) -> list[float]:
    return next(iter(_model().query_embed(text))).tolist()


def embed_passages(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in _model().passage_embed(texts)]
