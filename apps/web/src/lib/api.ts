import { parseSseChunk } from "@/lib/sse";
import type { Citation, IngestResult, Source } from "@/lib/types";

export const AGENT_URL =
  process.env.NEXT_PUBLIC_AGENT_URL?.replace(/\/+$/, "") ?? "http://localhost:8080";

export async function fetchSources(): Promise<Source[]> {
  const res = await fetch(`${AGENT_URL}/sources`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Could not load sources (${res.status})`);
  return (await res.json()) as Source[];
}

export async function ingestDocument(file: File): Promise<IngestResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${AGENT_URL}/ingest`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed (${res.status})`);
  return (await res.json()) as IngestResult;
}

export interface QueryHandlers {
  onSources?: (sources: Citation[]) => void;
  onToken?: (text: string) => void;
}

/**
 * Stream a grounded answer from the agent's /query SSE endpoint, dispatching
 * `sources` and `token` events to the handlers. Resolves when the stream ends.
 */
export async function streamAnswer(
  question: string,
  init: { sessionId?: string | null; kind?: string | null; signal?: AbortSignal },
  handlers: QueryHandlers,
): Promise<void> {
  const res = await fetch(`${AGENT_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: init.sessionId ?? null, kind: init.kind ?? null }),
    signal: init.signal,
  });
  if (!res.ok || !res.body) throw new Error(`Query failed (${res.status})`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const { events, rest } = parseSseChunk(buffer);
    buffer = rest;
    for (const ev of events) {
      if (ev.event === "sources") {
        handlers.onSources?.(JSON.parse(ev.data) as Citation[]);
      } else if (ev.event === "token") {
        handlers.onToken?.((JSON.parse(ev.data) as { text: string }).text);
      } else if (ev.event === "done") {
        return;
      }
    }
  }
}
