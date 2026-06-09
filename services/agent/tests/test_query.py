"""Integration tests for the non-agentic /query SSE endpoint with a mocked LLM."""
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

import app.agent.rag as rag
from app.main import app

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
    {
        "id": 2,
        "document_id": 7,
        "section": "Posology",
        "text": "One tablet daily.",
        "title": "Drug X SmPC",
        "source_uri": None,
        "score": 0.020,
    },
]


def test_query_streams_sources_then_grounded_answer(monkeypatch):
    async def fake_retrieve(question: str, k: int = 5, kind: str | None = None) -> list[dict]:
        return CHUNKS

    async def fake_stream(question: str, chunks: list[dict]) -> AsyncIterator[str]:
        for token in ["Do not ", "use it in ", "pregnancy."]:
            yield token

    monkeypatch.setattr(rag, "retrieve", fake_retrieve)
    monkeypatch.setattr(rag, "stream_completion", fake_stream)

    client = TestClient(app)
    r = client.post("/query", json={"question": "Is Drug X safe in pregnancy?"})

    assert r.status_code == 200
    body = r.text
    # citations are emitted up front so the UI can render sources
    assert "event: sources" in body
    assert "Drug X SmPC" in body
    assert "Contraindications" in body
    # the grounded answer tokens stream after
    assert "pregnancy." in body
    assert "event: done" in body


def test_query_refuses_and_skips_llm_when_no_context(monkeypatch):
    called = {"llm": False}

    async def fake_retrieve(question: str, k: int = 5, kind: str | None = None) -> list[dict]:
        return []

    async def fake_stream(question: str, chunks: list[dict]) -> AsyncIterator[str]:
        called["llm"] = True
        yield "this should never be sent"

    monkeypatch.setattr(rag, "retrieve", fake_retrieve)
    monkeypatch.setattr(rag, "stream_completion", fake_stream)

    client = TestClient(app)
    r = client.post("/query", json={"question": "What is the capital of France?"})

    assert r.status_code == 200
    assert "don't have enough information" in r.text.lower()
    assert called["llm"] is False  # guardrail v1: never call the model unsupported
