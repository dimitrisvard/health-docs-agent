"""Tests for the /sources and /ingest endpoints and the upload text extractor."""
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


def test_evals_endpoint_returns_latest_report(monkeypatch):
    report = {
        "run": {"id": 1, "commit_sha": "abc1234", "created_at": "2026-06-09T00:00:00"},
        "aggregates": {"hit_at_5": 0.8, "mrr": 0.7, "ndcg": 0.75, "faithfulness": 0.9},
        "results": [{"question": "q", "hit_at_k": True, "mrr": 1.0, "ndcg": 1.0, "faithfulness": 0.9}],
    }
    monkeypatch.setattr("app.main.latest_eval", lambda: report)
    r = TestClient(app).get("/evals")
    assert r.status_code == 200
    assert r.json()["aggregates"]["hit_at_5"] == 0.8


def test_evals_endpoint_handles_no_run(monkeypatch):
    monkeypatch.setattr("app.main.latest_eval", lambda: None)
    r = TestClient(app).get("/evals")
    assert r.status_code == 200
    assert r.json() is None
