from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import uuid4

import structlog
from fastapi import FastAPI, HTTPException, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.loop import answer_stream
from app.agent.rag import ingest_upload, list_sources
from app.obs.logging import configure_logging
from app.obs.tracing import configure_tracing
from app.reports import latest_eval

configure_logging()
app = FastAPI(title="health-docs-agent")
configure_tracing(app)


@app.middleware("http")
async def trace_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """One trace_id per request, bound to structlog so every turn log carries it."""
    trace_id = request.headers.get("x-trace-id") or uuid4().hex
    structlog.contextvars.bind_contextvars(trace_id=trace_id)
    try:
        response = await call_next(request)
    finally:
        structlog.contextvars.clear_contextvars()
    response.headers["x-trace-id"] = trace_id
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/sources")
async def sources() -> list[dict]:
    return await list_sources()


@app.get("/evals")
def evals() -> dict | None:
    return latest_eval()


class Query(BaseModel):
    question: str
    session_id: str | None = None
    kind: str | None = None


@app.post("/query")
async def query(q: Query) -> StreamingResponse:
    return StreamingResponse(
        answer_stream(q.question, q.session_id, q.kind),
        media_type="text/event-stream",
    )


@app.post("/ingest")
async def ingest(file: UploadFile) -> dict:
    raw = await file.read()
    try:
        return await ingest_upload(file.filename or "upload.txt", raw)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
