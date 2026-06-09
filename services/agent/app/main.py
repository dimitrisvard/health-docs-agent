from __future__ import annotations

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.loop import answer_stream
from app.agent.rag import ingest_upload, list_sources
from app.obs.logging import configure_logging
from app.reports import latest_eval

configure_logging()
app = FastAPI(title="health-docs-agent")


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
