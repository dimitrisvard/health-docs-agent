"""Agent loop on the Claude Agent SDK. Tools come from the FastMCP server (services/mcp).

LLM traffic routes through Cloudflare AI Gateway automatically when ANTHROPIC_BASE_URL
is set in the environment (the SDK respects the standard Anthropic env vars).
"""
from __future__ import annotations

import os
from collections.abc import AsyncIterator

from claude_agent_sdk import ClaudeAgentOptions, query

from app.agent.prompts import GROUNDED_HEALTH_SYSTEM_PROMPT

MCP_URL = os.environ.get("MCP_URL", "http://mcp:8000/mcp")
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

OPTIONS = ClaudeAgentOptions(
    model=MODEL,
    system_prompt=GROUNDED_HEALTH_SYSTEM_PROMPT,
    mcp_servers={"retrieval": {"type": "http", "url": MCP_URL}},
    allowed_tools=[
        "mcp__retrieval__hybrid_search",
        "mcp__retrieval__fetch_section",
        "mcp__retrieval__compare_documents",
        "mcp__retrieval__list_sources",
    ],
    max_turns=6,  # bound the loop (never omit in an unattended run)
)


async def answer_stream(question: str, session_id: str | None = None) -> AsyncIterator[str]:
    """Yield SSE frames as the agent plans, calls tools, and streams a grounded answer.

    TODO(Phase 4/6):
      - map SDK message types -> SSE frames (text deltas + tool events + sources)
      - run output guardrails on the final answer (grounded-only, not-medical-advice)
      - persist the turn to the `messages` table (tool_calls, sources, tokens, latency)
    """
    async for message in query(prompt=question, options=OPTIONS):
        yield f"data: {message}\n\n"
