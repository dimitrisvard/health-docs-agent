"use client";

import { ArrowUp, MessageSquareText, ShieldCheck, Square } from "lucide-react";
import { type FormEvent, type KeyboardEvent, useEffect, useRef, useState } from "react";

import { ChatMessage } from "@/components/chat-message";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { KIND_LABEL, type SourceKind } from "@/lib/types";
import { useChat } from "@/lib/use-chat";

const SUGGESTIONS = [
  "What are the exclusion criteria in the trial?",
  "List the contraindications for this drug.",
  "Compare the dosing guidance across documents.",
];

export function ChatPanel({ scope }: { scope: SourceKind | null }) {
  const { messages, isStreaming, send, stop } = useChat();
  const [input, setInput] = useState("");
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isStreaming) return;
    send(input, { kind: scope });
    setInput("");
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <section className="flex h-full min-w-0 flex-col">
      <div ref={threadRef} className="scrollbar-thin flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
          {messages.length === 0 ? (
            <div className="pt-10">
              <EmptyState
                icon={<MessageSquareText className="size-5" />}
                title="Ask across your documents"
                description="Answers are grounded only in the ingested corpus and cite the chunks they used."
              />
              <div className="mx-auto mt-2 flex max-w-md flex-col gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s, { kind: scope })}
                    className="rounded-lg border bg-card px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-6">
              {messages.map((m) => (
                <ChatMessage key={m.id} message={m} />
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="border-t bg-background/80 backdrop-blur">
        <form onSubmit={submit} className="mx-auto w-full max-w-3xl px-4 py-3 sm:px-6">
          {scope && (
            <p className="mb-2 text-xs text-muted-foreground">
              Scoped to <span className="font-medium text-foreground">{KIND_LABEL[scope]}</span> documents
            </p>
          )}
          <div className="flex items-end gap-2 rounded-xl border bg-card p-2 shadow-sm focus-within:ring-2 focus-within:ring-ring">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              placeholder="Ask a question about the corpus…"
              className="max-h-40 min-h-[2.25rem] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-muted-foreground"
            />
            {isStreaming ? (
              <Button type="button" variant="subtle" size="icon" onClick={stop} aria-label="Stop generating">
                <Square className="size-3.5" />
              </Button>
            ) : (
              <Button type="submit" size="icon" disabled={!input.trim()} aria-label="Send question">
                <ArrowUp />
              </Button>
            )}
          </div>
          <p className="mt-2 flex items-center justify-center gap-1.5 text-center text-[11px] text-muted-foreground">
            <ShieldCheck className="size-3" />
            Grounded in your documents · not medical advice. Enter to send, Shift+Enter for a new line.
          </p>
        </form>
      </div>
    </section>
  );
}
