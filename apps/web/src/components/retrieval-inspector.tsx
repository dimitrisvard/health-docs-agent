"use client";

import { ChevronDown, ScanSearch } from "lucide-react";
import { useState } from "react";

import type { Citation } from "@/lib/types";
import { cn } from "@/lib/utils";

export function RetrievalInspector({ citations }: { citations: Citation[] }) {
  const [open, setOpen] = useState(false);
  if (citations.length === 0) return null;

  const max = Math.max(...citations.map((c) => c.score ?? 0), 1e-9);

  return (
    <div className="mt-3 overflow-hidden rounded-lg border bg-muted/30">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-2 px-3 py-2 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <span className="inline-flex items-center gap-1.5">
          <ScanSearch className="size-3.5" />
          Retrieval · hybrid_search · {citations.length} chunks
        </span>
        <ChevronDown className={cn("size-4 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <ul className="space-y-2.5 border-t px-3 py-3">
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
  );
}
