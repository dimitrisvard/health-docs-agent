export interface SseEvent {
  event: string;
  data: string;
}

/**
 * Parse a buffer of concatenated SSE frames (delimited by a blank line).
 * Returns the complete events plus any unfinished trailing partial frame,
 * so a caller can carry `rest` forward across network chunks.
 */
export function parseSseChunk(buffer: string): { events: SseEvent[]; rest: string } {
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";
  const events: SseEvent[] = [];

  for (const part of parts) {
    if (!part.trim()) continue;
    let event = "message";
    const dataLines: string[] = [];
    for (const line of part.split("\n")) {
      if (line.startsWith("event:")) event = line.slice("event:".length).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice("data:".length).replace(/^ /, ""));
    }
    events.push({ event, data: dataLines.join("\n") });
  }

  return { events, rest };
}
