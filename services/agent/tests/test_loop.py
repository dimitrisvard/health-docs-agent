"""Tests for the agentic /query path (Claude Agent SDK loop).

The SDK is faked via sys.modules so these run without the Node-backed package: the
loop dispatches on message class name, so fakes only need matching __class__.__name__.
"""
import json
import sys
import types

from fastapi.testclient import TestClient

from app.main import app


class StreamEvent:
    def __init__(self, event: dict) -> None:
        self.event = event


class AssistantMessage:
    def __init__(self, content: list) -> None:
        self.content = content


class UserMessage:
    def __init__(self, content: list) -> None:
        self.content = content


class ResultMessage:
    def __init__(self) -> None:
        self.subtype = "success"


class ToolUseBlock:
    def __init__(self, name: str, tool_input: dict) -> None:
        self.name = name
        self.input = tool_input
        self.id = "toolu_1"


class ToolResultBlock:
    def __init__(self, content) -> None:
        self.content = content
        self.tool_use_id = "toolu_1"
        self.is_error = False


def _install_fake_sdk(monkeypatch, messages: list, captured: dict | None = None) -> None:
    async def fake_query(*, prompt, options):
        if captured is not None:
            captured["prompt"] = prompt
            captured["options"] = options
        for message in messages:
            yield message

    fake = types.ModuleType("claude_agent_sdk")
    fake.query = fake_query  # type: ignore[attr-defined]
    fake.ClaudeAgentOptions = lambda **kwargs: kwargs  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", fake)


def test_agentic_query_maps_messages_to_sse_frames(monkeypatch):
    chunk = {
        "id": 1,
        "document_id": 7,
        "title": "Drug X SmPC",
        "section": "Contraindications",
        "score": 0.031,
        "text": "Do not use in pregnancy.",
    }
    messages = [
        StreamEvent({"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Based on "}}),
        AssistantMessage([ToolUseBlock("mcp__retrieval__hybrid_search", {"query": "pregnancy"})]),
        UserMessage([ToolResultBlock([{"type": "text", "text": json.dumps([chunk])}])]),
        StreamEvent({"type": "content_block_delta", "delta": {"type": "text_delta", "text": "the label, avoid it."}}),
        ResultMessage(),
    ]
    _install_fake_sdk(monkeypatch, messages)

    r = TestClient(app).post("/query", json={"question": "Is Drug X safe in pregnancy?"})

    assert r.status_code == 200
    body = r.text
    # streamed answer tokens
    assert "event: token" in body and "Based on " in body and "avoid it." in body
    # the tool the agent fired
    assert "event: tool" in body and "hybrid_search" in body
    # citations derived from the tool result
    assert "event: sources" in body and "Drug X SmPC" in body and "Contraindications" in body
    assert "event: done" in body


def test_agentic_query_scopes_prompt_by_kind(monkeypatch):
    captured: dict = {}
    _install_fake_sdk(monkeypatch, [ResultMessage()], captured)

    r = TestClient(app).post("/query", json={"question": "List the contraindications.", "kind": "drug_label"})

    assert r.status_code == 200
    assert "drug_label" in captured["prompt"]


def test_agentic_query_declines_personal_medical_advice(monkeypatch):
    captured: dict = {}
    _install_fake_sdk(monkeypatch, [ResultMessage()], captured)

    r = TestClient(app).post("/query", json={"question": "Should I take ibuprofen for my back pain?"})

    assert r.status_code == 200
    assert "personal medical advice" in r.text.lower()
    assert "prompt" not in captured  # guardrail short-circuits before the agent runs


class _FakeCursor:
    def __init__(self, store: dict) -> None:
        self.store = store

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def execute(self, sql: str, params: tuple | None = None) -> None:
        self.store["execute"].append((sql, params))


class _FakeConn:
    def __init__(self) -> None:
        self.store: dict = {"execute": [], "commits": 0, "closed": False}

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self.store)

    def commit(self) -> None:
        self.store["commits"] += 1

    def close(self) -> None:
        self.store["closed"] = True


def test_persist_turn_writes_user_and_assistant_rows():
    import app.agent.loop as loop

    conn = _FakeConn()
    loop._persist_turn(
        session_id="s1",
        question="What are the contraindications?",
        answer="Avoid in pregnancy.",
        tool_calls=[{"name": "mcp__retrieval__hybrid_search", "input": {}}],
        sources=[{"id": 1, "title": "Drug X SmPC"}],
        usage={"input_tokens": 10, "output_tokens": 20},
        latency_ms=42,
        conn=conn,
    )

    execs = conn.store["execute"]
    assert any(p and "user" in p for _, p in execs)
    assistant = next(p for _, p in execs if p and "assistant" in p)
    assert "hybrid_search" in assistant[3]  # tool_calls serialized as JSON
    assert assistant[6] == 10 and assistant[7] == 20  # tokens in/out
    assert conn.store["commits"] >= 1
    assert conn.store["closed"] is False  # injected conn is not owned/closed
