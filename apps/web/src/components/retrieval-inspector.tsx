"use client";

import { ChevronDown, ScanSearch } from "lucide-react";
import { useState } from "react";

import type { Citation } from "@/lib/types";
import { cn } from "@/lib/utils";

function toolLabel(name: string): string {
  return name.replace(/^mcp__\w+__/, "");
}

export function RetrievalInspector({
  citations,
  tools = [],
}: {
  citations: Citation[];
  tools?: string[];
}) {
  const [open, setOpen] = useState(false);
  if (citations.length === 0 && tools.length === 0) return null;

  const max = Math.max(...citations.map((c) => c.score ?? 0), 1e-9);
  const fired = Array.from(new Set(tools));

  return (
    <div className="mt-3 overflow-hidden rounded-lg border bg-muted/30">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-2 px-3 py-2 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <span className="inline-flex items-center gap-1.5">
          <ScanSearch className="size-3.5" />
          Retrieval
          {fired.length > 0 ? ` · ${fired.map(toolLabel).join(", ")}` : ""} · {citations.length} chunks
        </span>
        <ChevronDown className={cn("size-4 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="space-y-3 border-t px-3 py-3">
          {fired.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {fired.map((t) => (
                <span
                  key={t}
                  className="rounded-md bg-primary/10 px-2 py-0.5 font-mono text-[10px] text-primary"
                >
                  {toolLabel(t)}
                </span>
              ))}
            </div>
          )}

          {citations.length > 0 && (
            <ul className="space-y-2.5">
              {citations.map((c) => (
                <li key={c.id} className="text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate font-medium text-foreground">
                      <span className="font-mono text-[10px] text-primary">#{c.id}</span> {c.title}
                      {c.section ? ` · ${c.section}` : ""}
                    </span>
                    <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                      {(c.score ?? 0).toFixed(4)}
                    </span>
                  </div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-border">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{ width: `${Math.max(6, ((c.score ?? 0) / max) * 100)}%` }}
                    />
                  </div>
                  {c.text && <p className="mt-1 line-clamp-2 text-muted-foreground">{c.text}</p>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
