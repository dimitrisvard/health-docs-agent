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
