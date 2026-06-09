import { describe, expect, it } from "vitest";

import { parseSseChunk } from "@/lib/sse";

describe("parseSseChunk", () => {
  it("parses complete named events and keeps the trailing partial", () => {
    const buffer =
      'event: sources\ndata: [{"id":1}]\n\n' + 'event: token\ndata: {"text":"Hello"}\n\n' + "event: token\ndata: {";
    const { events, rest } = parseSseChunk(buffer);

    expect(events).toEqual([
      { event: "sources", data: '[{"id":1}]' },
      { event: "token", data: '{"text":"Hello"}' },
    ]);
    expect(rest).toBe('event: token\ndata: {');
  });

  it("defaults to the message event and strips one leading data space", () => {
    const { events } = parseSseChunk("data: plain\n\n");
    expect(events).toEqual([{ event: "message", data: "plain" }]);
  });

  it("returns no events when only a partial frame is present", () => {
    const { events, rest } = parseSseChunk("event: token\ndata: {\"text\"");
    expect(events).toHaveLength(0);
    expect(rest).toContain("token");
  });
});
