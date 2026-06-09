# Architecture

A multi-step, tool-calling agent over a hybrid-retrieval corpus. The retrieval MCP server
is standalone and reused by both the agent service and Claude Code (via `.mcp.json`).

## Components

- **apps/web** — Next.js 15 + TypeScript + Tailwind. Token-streaming chat with citation
  chips, a retrieval inspector (which tools fired + retrieved chunks + RRF score bars), a
  corpus sidebar with kind filter and upload, and the `/evals` dashboard. Talks to the
  agent over SSE.
- **services/agent** — FastAPI + Claude Agent SDK agent loop. Streams over SSE; owns the
  guardrails (grounded-only, not-medical-advice, prompt-injection defense) and the
  observability layer (OpenTelemetry spans, `structlog` with a `trace_id`, the `messages`
  table). LLM traffic routes through Cloudflare AI Gateway via `ANTHROPIC_BASE_URL`.
- **services/mcp** — FastMCP server exposing `hybrid_search`, `fetch_section`,
  `compare_documents`, `list_sources`. Owns ingestion (structure-aware chunking +
  FastEmbed `bge-base-en-v1.5` embeddings) and hybrid retrieval (pgvector dense + Postgres
  full-text, fused with Reciprocal Rank Fusion).
- **Postgres 16 + pgvector** — `documents`, `chunks` (dense `vector(768)` + `tsvector`),
  `messages`, `eval_runs` / `eval_results`.
- **evals** — golden set + runner (hit@k / MRR / nDCG + LLM-as-judge faithfulness), gated
  in CI and rendered on `/evals`.

## System

```mermaid
flowchart TB
    subgraph Client["Browser"]
        UI["Next.js 15 UI<br/>chat • citations • retrieval inspector • eval dashboard"]
    end
    subgraph AgentSvc["Agent service (FastAPI, Docker)"]
        LOOP["Agent loop<br/>Claude Agent SDK — multi-step tool calling"]
        GRD["Guardrails<br/>grounded-only • not-medical-advice • injection defense"]
    end
    subgraph MCPSvc["Retrieval MCP server (FastMCP, Docker)"]
        T1["tool: hybrid_search"]
        T2["tool: fetch_section"]
        T3["tool: compare_documents"]
        T4["tool: list_sources"]
    end
    subgraph Data["Data layer (Docker)"]
        PG[("Postgres<br/>pgvector (dense) + full-text (lexical)<br/>docs • chunks • logs • eval runs")]
        EMB["FastEmbed<br/>bge-base-en-v1.5 (768d)"]
    end
    subgraph Edge["Cloudflare"]
        AIG["AI Gateway<br/>logs • cost • cache • spend limits"]
    end
    LLM["Anthropic — Claude Sonnet"]
    CC["Claude Code / Desktop<br/>reuses the SAME MCP server"]

    UI -->|query SSE| LOOP
    LOOP -->|tool calls| T1 & T2 & T3 & T4
    T1 --> EMB
    EMB --> PG
    T1 --> PG
    T2 --> PG
    T3 --> PG
    LOOP --> GRD
    LOOP -->|messages via ANTHROPIC_BASE_URL| AIG
    AIG --> LLM
    CC -.reuses.-> MCPSvc
```

## Query path (agentic + hybrid)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Next.js
    participant AG as Agent (Claude Agent SDK)
    participant GW as CF AI Gateway
    participant LLM as Claude Sonnet
    participant MCP as FastMCP retrieval
    participant DB as Postgres (pgvector + FTS)

    U->>FE: Ask a question
    FE->>AG: POST /query (SSE)
    AG->>GW: plan turn (messages)
    GW->>LLM: forward (+ log, meter)
    LLM-->>GW: tool_use: hybrid_search(query)
    GW-->>AG: tool call
    AG->>MCP: hybrid_search(query)
    MCP->>DB: dense top-k (cosine) + lexical top-k (FTS)
    DB-->>MCP: two ranked lists
    MCP->>MCP: fuse via Reciprocal Rank Fusion
    MCP-->>AG: chunks + scores
    AG->>GW: tool_result → continue
    GW->>LLM: synthesize grounded answer
    LLM-->>GW: streamed, cited answer
    GW-->>AG: token stream
    AG->>AG: guardrails (grounded-only, not-medical-advice)
    AG-->>FE: SSE: tokens + sources
    FE-->>U: streamed answer + citations + inspector
```
