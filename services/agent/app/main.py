from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.loop import answer_stream
from app.obs.logging import configure_logging

configure_logging()
app = FastAPI(title="health-docs-agent")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


class Query(BaseModel):
    question: str
    session_id: str | None = None


@app.post("/query")
async def query(q: Query) -> StreamingResponse:
    return StreamingResponse(
        answer_stream(q.question, q.session_id),
        media_type="text/event-stream",
    )
