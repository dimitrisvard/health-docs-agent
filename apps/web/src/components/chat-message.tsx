"use client";

import { AlertCircle, Check, Copy } from "lucide-react";
import { useState } from "react";

import { CitationChips } from "@/components/citation-chips";
import { RetrievalInspector } from "@/components/retrieval-inspector";
import { Button } from "@/components/ui/button";
import type { ChatMessage as Msg } from "@/lib/types";

export function ChatMessage({ message }: { message: Msg }) {
  const [copied, setCopied] = useState(false);

  if (message.role === "user") {
    return (
      <div className="flex animate-fade-in justify-end">
        <div className="max-w-[80%] whitespace-pre-wrap rounded-xl rounded-br-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground shadow-sm">
          {message.content}
        </div>
      </div>
    );
  }

  const streaming = message.status === "streaming";
  const showDots = streaming && message.content === "";
  const hasCitations = (message.citations?.length ?? 0) > 0;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <div className="group flex animate-fade-in flex-col gap-2">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span className="inline-flex size-5 items-center justify-center rounded-full bg-primary/12 text-[10px] font-semibold text-primary">
          A
        </span>
        Assistant
      </div>

      <div className="rounded-xl rounded-tl-sm border bg-card px-4 py-3 text-sm leading-relaxed shadow-sm">
        {message.status === "error" ? (
          <p className="flex items-center gap-2 text-destructive">
            <AlertCircle className="size-4 shrink-0" />
            {message.content}
          </p>
        ) : showDots ? (
          <TypingDots />
        ) : (
          <p className="whitespace-pre-wrap">
            {message.content}
            {streaming && (
              <span className="ml-0.5 inline-block h-4 w-0.5 -translate-y-px animate-blink bg-primary align-middle" />
            )}
          </p>
        )}

        {hasCitations && (
          <>
            <CitationChips citations={message.citations!} className="mt-3" />
            <RetrievalInspector citations={message.citations!} />
          </>
        )}
      </div>

      {message.status === "done" && message.content && (
        <div className="opacity-0 transition-opacity group-hover:opacity-100">
          <Button
            variant="ghost"
            size="sm"
            onClick={copy}
            className="h-7 gap-1.5 text-xs text-muted-foreground"
          >
            {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
            {copied ? "Copied" : "Copy answer"}
          </Button>
        </div>
      )}
    </div>
  );
}

function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1" aria-label="Assistant is typing">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="size-1.5 animate-blink rounded-full bg-muted-foreground"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </span>
  );
}
