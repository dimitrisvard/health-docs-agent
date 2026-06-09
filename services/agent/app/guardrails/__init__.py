"""Output-side guardrails.

Phase 2 ships guardrail v1: refuse to answer when retrieval surfaced no supporting
context, so the model is never asked to fill gaps from prior knowledge.

TODO(Phase 6): score thresholds, an explicit not-medical-advice output check, and
prompt-injection detection (document text is data, never instructions). Write tests FIRST:
  - no-context question -> refusal
  - document containing 'ignore previous instructions' -> treated as data, ignored
"""
from __future__ import annotations

INSUFFICIENT_CONTEXT = (
    "I don't have enough information in the provided documents to answer that."
)


def is_supported(chunks: list[dict]) -> bool:
    """A grounded answer requires at least one retrieved chunk."""
    return len(chunks) > 0
