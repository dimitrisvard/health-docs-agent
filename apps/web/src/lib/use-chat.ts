"use client";

import { useCallback, useRef, useState } from "react";

import { streamAnswer } from "@/lib/api";
import type { ChatMessage, Citation } from "@/lib/types";

let seq = 0;
const nextId = () => `m${Date.now().toString(36)}-${seq++}`;

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(
    async (question: string, opts?: { kind?: string | null }) => {
      const q = question.trim();
      if (!q || abortRef.current) return;

      const assistantId = nextId();
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: "user", content: q },
        { id: assistantId, role: "assistant", content: "", citations: [], tools: [], status: "streaming" },
      ]);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;
      const patch = (p: Partial<ChatMessage>) =>
        setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, ...p } : m)));

      try {
        let content = "";
        let citations: Citation[] = [];
        let tools: string[] = [];
        await streamAnswer(
          q,
          { signal: controller.signal, kind: opts?.kind ?? null },
          {
            onSources: (s) => {
              citations = s;
              patch({ citations: s });
            },
            onToken: (t) => {
              content += t;
              patch({ content });
            },
            onTool: (name) => {
              tools = [...tools, name];
              patch({ tools });
            },
          },
        );
        patch({ content, citations, tools, status: "done" });
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          patch({
            status: "error",
            content: "Couldn't reach the agent. Make sure it's running, then try again.",
          });
        } else {
          patch({ status: "done" });
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [],
  );

  const stop = useCallback(() => abortRef.current?.abort(), []);

  return { messages, isStreaming, send, stop };
}
