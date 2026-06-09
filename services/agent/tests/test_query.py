"""Tests for the non-agentic RAG pipeline (rag.answer_stream).

This path is no longer wired to /query (Phase 4 moved that to the agentic loop), but
it remains the grounded baseline + guardrail v1, so it is exercised directly here.
"""
import asyncio
from collections.abc import AsyncIterator

import app.agent.rag as rag

CHUNKS = [
    {
        "id": 1,
        "document_id": 7,
        "section": "Contraindications",
        "text": "Do not use in pregnancy.",
        "title": "Drug X SmPC",
        "source_uri": None,
        "score": 0.031,
    },
]


def _drain(agen: AsyncIterator[str]) -> str:
    async def go() -> list[str]:
        return [frame async for frame in agen]

    return "".join(asyncio.run(go()))


def test_rag_streams_sources_then_grounded_answer(monkeypatch):
    async def fake_retrieve(question: str, k: int = 5, kind: str | None = None) -> list[dict]:
        return CHUNKS

    async def fake_stream(question: str, chunks: list[dict]) -> AsyncIterator[str]:
        for token in ["Do not ", "use it in ", "pregnancy."]:
            yield token

    monkeypatch.setattr(rag, "retrieve", fake_retrieve)
    monkeypatch.setattr(rag, "stream_completion", fake_stream)

    body = _drain(rag.answer_stream("Is Drug X safe in pregnancy?"))
    assert "event: sources" in body
    assert "Drug X SmPC" in body and "Contraindications" in body
    assert "pregnancy." in body
    assert "event: done" in body


def test_rag_refuses_and_skips_llm_when_no_context(monkeypatch):
    called = {"llm": False}

    async def fake_retrieve(question: str, k: int = 5, kind: str | None = None) -> list[dict]:
        return []

    async def fake_stream(question: str, chunks: list[dict]) -> AsyncIterator[str]:
        called["llm"] = True
        yield "this should never be sent"

    monkeypatch.setattr(rag, "retrieve", fake_retrieve)
    monkeypatch.setattr(rag, "stream_completion", fake_stream)

    body = _drain(rag.answer_stream("What is the capital of France?"))
    assert "don't have enough information" in body.lower()
    assert called["llm"] is False
