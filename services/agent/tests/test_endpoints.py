"""Tests for the /sources and /ingest endpoints and the upload text extractor."""
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.agent.rag import _extract_text
from app.main import app


def test_extract_text_decodes_plaintext():
    assert _extract_text("note.txt", b"hello world") == "hello world"
    assert _extract_text("guide.md", b"## H\nbody") == "## H\nbody"


def test_extract_text_rejects_unsupported_type():
    with pytest.raises(ValueError):
        _extract_text("malware.exe", b"\x00\x01")


def test_sources_endpoint_proxies_mcp(monkeypatch):
    async def fake_list_sources() -> list[dict]:
        return [{"id": 1, "kind": "trial", "title": "ACME Trial", "source_uri": None}]

    monkeypatch.setattr("app.main.list_sources", fake_list_sources)
    client = TestClient(app)
    r = client.get("/sources")
    assert r.status_code == 200
    assert r.json()[0]["title"] == "ACME Trial"


def test_ingest_endpoint_forwards_upload(monkeypatch):
    captured: dict = {}

    async def fake_ingest_upload(filename: str, raw: bytes) -> dict:
        captured["filename"] = filename
        return {"document_id": 5, "title": "note", "kind": "guideline", "chunks": 3}

    monkeypatch.setattr("app.main.ingest_upload", fake_ingest_upload)
    client = TestClient(app)
    r = client.post("/ingest", files={"file": ("note.txt", b"hello", "text/plain")})
    assert r.status_code == 200
    assert r.json()["chunks"] == 3
    assert captured["filename"] == "note.txt"


def test_ingest_endpoint_returns_415_on_unsupported(monkeypatch):
    async def fake_ingest_upload(filename: str, raw: bytes) -> dict:
        raise ValueError(f"Unsupported file type: {filename}")

    monkeypatch.setattr("app.main.ingest_upload", fake_ingest_upload)
    client = TestClient(app)
    r = client.post("/ingest", files={"file": ("x.exe", b"x", "application/octet-stream")})
    assert r.status_code == 415


def test_query_forwards_kind_scope(monkeypatch):
    captured: dict = {}

    async def fake_retrieve(question: str, k: int = 5, kind: str | None = None) -> list[dict]:
        captured["kind"] = kind
        return [
            {
                "id": 1,
                "document_id": 1,
                "section": "S",
                "text": "t",
                "title": "T",
                "source_uri": None,
                "score": 0.02,
            }
        ]

    async def fake_stream(question: str, chunks: list[dict]) -> AsyncIterator[str]:
        yield "ok"

    monkeypatch.setattr("app.agent.rag.retrieve", fake_retrieve)
    monkeypatch.setattr("app.agent.rag.stream_completion", fake_stream)
    client = TestClient(app)
    r = client.post("/query", json={"question": "what is x?", "kind": "trial"})
    assert r.status_code == 200
    assert captured["kind"] == "trial"
