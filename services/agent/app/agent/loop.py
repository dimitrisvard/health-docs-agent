"""Agentic loop on the Claude Agent SDK (Phase 4).

The model decides when to call the FastMCP retrieval tools (hybrid_search,
fetch_section, compare_documents, list_sources). The loop is bounded by max_turns
and an explicit allowed_tools list. SDK messages are mapped to the SAME SSE frames
the non-agentic path emits (`sources`, `token`, `done`) plus `tool` events, so the
frontend renders both identically.

LLM traffic routes through Cloudflare AI Gateway when ANTHROPIC_BASE_URL is set; the
SDK respects the standard Anthropic env vars. The SDK drives the Claude Code engine,
which needs the Node CLI in the container (see services/agent/Dockerfile).
"""
from __future__ import annotations

import json
import os
import time
from collections.abc import AsyncIterator
from typing import Any

import structlog

from app.agent.prompts import GROUNDED_HEALTH_SYSTEM_PROMPT

log = structlog.get_logger()

MCP_URL = os.environ.get("MCP_URL", "http://mcp:8000/mcp")
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_TURNS = int(os.environ.get("AGENT_MAX_TURNS", "6"))

ALLOWED_TOOLS = [
    "mcp__retrieval__hybrid_search",
    "mcp__retrieval__fetch_section",
    "mcp__retrieval__compare_documents",
    "mcp__retrieval__list_sources",
]


def _options() -> Any:
    from claude_agent_sdk import ClaudeAgentOptions  # lazy: SDK drives the Node CLI

    return ClaudeAgentOptions(
        model=MODEL,
        system_prompt=GROUNDED_HEALTH_SYSTEM_PROMPT,
        mcp_servers={"retrieval": {"type": "http", "url": MCP_URL}},
        allowed_tools=ALLOWED_TOOLS,
        max_turns=MAX_TURNS,
        include_partial_messages=True,  # token-level text deltas via StreamEvent
    )


def _sse(data: str, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {data}\n\n"


def _delta_text(event: Any) -> str:
    """Pull assistant text from a raw Claude streaming event (StreamEvent.event)."""
    if isinstance(event, dict) and event.get("type") == "content_block_delta":
        delta = event.get("delta", {})
        if isinstance(delta, dict) and delta.get("type") == "text_delta":
            return delta.get("text", "") or ""
    return ""


def _as_chunks(parsed: Any) -> list[dict]:
    if isinstance(parsed, list):
        return [c for c in parsed if isinstance(c, dict)]
    if isinstance(parsed, dict):  # compare_documents returns {doc_id: [chunk, ...]}
        out: list[dict] = []
        for value in parsed.values():
            if isinstance(value, list):
                out.extend(c for c in value if isinstance(c, dict))
        return out
    return []


def _chunks_from_tool_result(content: Any) -> list[dict]:
    """Best-effort extraction of retrieved chunks from an MCP tool result."""
    if isinstance(content, str):
        try:
            return _as_chunks(json.loads(content))
        except ValueError:
            return []
    chunks: list[dict] = []
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                try:
                    chunks.extend(_as_chunks(json.loads(part["text"])))
                except ValueError:
                    continue
            elif isinstance(part, dict) and "id" in part:
                chunks.append(part)
    return chunks


def _citation(chunk: dict) -> dict:
    return {
        "id": chunk.get("id"),
        "document_id": chunk.get("document_id"),
        "title": chunk.get("title"),
        "section": chunk.get("section"),
        "score": chunk.get("score"),
        "text": chunk.get("text"),
    }


async def answer_stream(
    question: str, session_id: str | None = None, kind: str | None = None
) -> AsyncIterator[str]:
    """Run the bounded agentic loop and map SDK messages to SSE frames."""
    from claude_agent_sdk import query  # lazy: keeps imports light and the path mockable

    started = time.monotonic()
    prompt = question if not kind else f"{question}\n\nScope the search to documents of kind '{kind}'."
    citations: dict[Any, dict] = {}
    tools_used: list[str] = []

    async for message in query(prompt=prompt, options=_options()):
        name = type(message).__name__
        if name == "StreamEvent":
            text = _delta_text(getattr(message, "event", {}))
            if text:
                yield _sse(json.dumps({"text": text}), event="token")
        elif name == "AssistantMessage":
            for block in getattr(message, "content", None) or []:
                if type(block).__name__ == "ToolUseBlock":
                    tool = getattr(block, "name", "")
                    tools_used.append(tool)
                    yield _sse(json.dumps({"name": tool, "input": getattr(block, "input", {})}), event="tool")
        elif name == "UserMessage":
            content = getattr(message, "content", None)
            found: list[dict] = []
            if isinstance(content, list):
                for block in content:
                    if type(block).__name__ == "ToolResultBlock":
                        found.extend(_chunks_from_tool_result(getattr(block, "content", None)))
            for chunk in found:
                cite = _citation(chunk)
                if cite["id"] is not None:
                    citations[cite["id"]] = cite
            if found:
                yield _sse(json.dumps(list(citations.values())), event="sources")

    yield _sse("{}", event="done")
    log.info(
        "agent_answered",
        q_len=len(question),
        tools=tools_used,
        sources=len(citations),
        latency_ms=int((time.monotonic() - started) * 1000),
    )
