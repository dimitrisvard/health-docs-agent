"""Agentic loop on the Claude Agent SDK (Phase 4) + guardrails/observability (Phase 6).

The model decides when to call the FastMCP retrieval tools (hybrid_search, fetch_section,
compare_documents, list_sources), bounded by max_turns and an explicit allowed_tools list.
SDK messages map to the SSE frames the UI consumes (`sources`, `token`, `done`) plus `tool`.

Guardrails: decline out-of-scope personal clinical asks up front; treat document text as
data and log (never obey) injection attempts in retrieved chunks. Observability: a span per
agent turn, a `trace_id` carried via structlog, and the turn persisted to the messages table.

LLM traffic routes through Cloudflare AI Gateway when ANTHROPIC_BASE_URL is set; the SDK
drives the Claude Code engine, which needs the Node CLI in the container (see Dockerfile).
"""
from __future__ import annotations

import json
import os
import time
from collections.abc import AsyncIterator
from typing import Any

import structlog

from app.agent.prompts import GROUNDED_HEALTH_SYSTEM_PROMPT
from app.guardrails import NOT_MEDICAL_ADVICE, contains_injection, is_medical_advice_request
from app.obs.tracing import span

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


def _persist_turn(
    session_id: str | None,
    question: str,
    answer: str,
    tool_calls: list[dict],
    sources: list[dict],
    usage: dict,
    latency_ms: int,
    conn: Any = None,
) -> None:
    """Write the user + assistant turn to the messages table. Best-effort; `conn` injectable."""
    owns = conn is None
    if owns:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return
        import psycopg

        conn = psycopg.connect(db_url)
    trace_id = structlog.contextvars.get_contextvars().get("trace_id")
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages (session_id, role, content, trace_id) VALUES (%s, %s, %s, %s)",
                (session_id, "user", question, trace_id),
            )
            cur.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls, sources, trace_id, "
                "tokens_in, tokens_out, latency_ms) "
                "VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s)",
                (
                    session_id,
                    "assistant",
                    answer,
                    json.dumps(tool_calls),
                    json.dumps(sources),
                    trace_id,
                    usage.get("input_tokens"),
                    usage.get("output_tokens"),
                    latency_ms,
                ),
            )
        conn.commit()
    finally:
        if owns:
            conn.close()


async def answer_stream(
    question: str, session_id: str | None = None, kind: str | None = None
) -> AsyncIterator[str]:
    """Run the bounded agentic loop and map SDK messages to SSE frames."""
    started = time.monotonic()

    # Input guardrail: decline out-of-scope personal clinical / diagnostic requests.
    if is_medical_advice_request(question):
        log.info("refused_medical_advice", q_len=len(question))
        yield _sse(json.dumps([]), event="sources")
        yield _sse(json.dumps({"text": NOT_MEDICAL_ADVICE}), event="token")
        yield _sse("{}", event="done")
        return

    from claude_agent_sdk import query  # lazy: keeps imports light and the path mockable

    prompt = question if not kind else f"{question}\n\nScope the search to documents of kind '{kind}'."
    citations: dict[Any, dict] = {}
    tool_calls: list[dict] = []
    answer_parts: list[str] = []
    usage: dict = {}

    with span("agent.query", question_len=len(question), kind=kind or ""):
        async for message in query(prompt=prompt, options=_options()):
            name = type(message).__name__
            if name == "StreamEvent":
                text = _delta_text(getattr(message, "event", {}))
                if text:
                    answer_parts.append(text)
                    yield _sse(json.dumps({"text": text}), event="token")
            elif name == "AssistantMessage":
                for block in getattr(message, "content", None) or []:
                    if type(block).__name__ == "ToolUseBlock":
                        tool = getattr(block, "name", "")
                        tool_calls.append({"name": tool, "input": getattr(block, "input", {})})
                        yield _sse(json.dumps({"name": tool, "input": getattr(block, "input", {})}), event="tool")
            elif name == "UserMessage":
                content = getattr(message, "content", None)
                found: list[dict] = []
                if isinstance(content, list):
                    for block in content:
                        if type(block).__name__ == "ToolResultBlock":
                            found.extend(_chunks_from_tool_result(getattr(block, "content", None)))
                for chunk in found:
                    if contains_injection(str(chunk.get("text", ""))):
                        log.warning("injection_in_context_ignored", chunk_id=chunk.get("id"))
                    cite = _citation(chunk)
                    if cite["id"] is not None:
                        citations[cite["id"]] = cite
                if found:
                    yield _sse(json.dumps(list(citations.values())), event="sources")
            elif name == "ResultMessage":
                result_usage = getattr(message, "usage", None)
                if isinstance(result_usage, dict):
                    usage = result_usage

    yield _sse("{}", event="done")
    latency_ms = int((time.monotonic() - started) * 1000)
    log.info(
        "agent_answered",
        tools=[t["name"] for t in tool_calls],
        sources=len(citations),
        tokens_in=usage.get("input_tokens"),
        tokens_out=usage.get("output_tokens"),
        latency_ms=latency_ms,
    )
    try:
        _persist_turn(
            session_id, question, "".join(answer_parts), tool_calls,
            list(citations.values()), usage, latency_ms,
        )
    except Exception as exc:  # noqa: BLE001 — persistence is best-effort observability
        log.warning("persist_failed", error=str(exc))
