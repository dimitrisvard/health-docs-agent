"""Non-agentic RAG pipeline (Phase 2): retrieve -> ground -> stream a cited answer.

This deterministic single-shot path is the grounded baseline that evals gate. Phase 4
swaps the /query entrypoint to the Claude Agent SDK loop (app/agent/loop.py), which lets
the model decide when to search, fetch a section, or compare documents.

Retrieval is delegated to the FastMCP server over HTTP — tools never live in the agent.
The LLM call routes through Cloudflare AI Gateway automatically when ANTHROPIC_BASE_URL
is set (the Anthropic SDK respects the standard env vars).
"""
from __future__ import annotations

import json
import os
import time
from collections.abc import AsyncIterator

import structlog

from app.agent.prompts import GROUNDED_HEALTH_SYSTEM_PROMPT
from app.guardrails import INSUFFICIENT_CONTEXT, is_supported

log = structlog.get_logger()

MCP_URL = os.environ.get("MCP_URL", "http://mcp:8000/mcp")
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
TOP_K = int(os.environ.get("RETRIEVAL_K", "5"))
MAX_TOKENS = int(os.environ.get("ANSWER_MAX_TOKENS", "1024"))


async def retrieve(question: str, k: int = TOP_K, kind: str | None = None) -> list[dict]:
    """Call the MCP retrieval server's hybrid_search tool over HTTP."""
    from fastmcp import Client  # lazy: keeps module import light and the path mockable

    async with Client(MCP_URL) as client:
        result = await client.call_tool("hybrid_search", {"query": question, "k": k, "kind": kind})
    data = result.data
    return list(data) if data else []


def _format_context(chunks: list[dict]) -> str:
    blocks = [
        f"[chunk {c['id']}] {c.get('title', '')} — {c.get('section', '')}\n{c['text']}".strip()
        for c in chunks
    ]
    return "\n\n".join(blocks)


def _citations(chunks: list[dict]) -> list[dict]:
    return [
        {
            "id": c["id"],
            "document_id": c.get("document_id"),
            "title": c.get("title"),
            "section": c.get("section"),
            "score": c.get("score"),
            "text": c.get("text"),
        }
        for c in chunks
    ]


async def stream_completion(question: str, chunks: list[dict]) -> AsyncIterator[str]:
    """Stream a grounded answer from the LLM (routed via Cloudflare AI Gateway)."""
    from anthropic import AsyncAnthropic  # lazy: env-configured (ANTHROPIC_BASE_URL / _API_KEY)

    client = AsyncAnthropic()
    user = f"Context:\n{_format_context(chunks)}\n\nQuestion: {question}"
    async with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=GROUNDED_HEALTH_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


def _sse(data: str, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {data}\n\n"


async def answer_stream(question: str, session_id: str | None = None) -> AsyncIterator[str]:
    """Yield SSE frames: a `sources` event, then `token` events, then `done`."""
    started = time.monotonic()
    chunks = await retrieve(question)
    yield _sse(json.dumps(_citations(chunks)), event="sources")

    if not is_supported(chunks):
        log.info("refused_unsupported", q_len=len(question), chunks=0)
        yield _sse(json.dumps({"text": INSUFFICIENT_CONTEXT}), event="token")
        yield _sse("{}", event="done")
        return

    async for token in stream_completion(question, chunks):
        yield _sse(json.dumps({"text": token}), event="token")
    yield _sse("{}", event="done")
    log.info(
        "answered",
        q_len=len(question),
        chunks=len(chunks),
        chunk_ids=[c["id"] for c in chunks],
        latency_ms=int((time.monotonic() - started) * 1000),
    )
