"use client";

import { FileStack, Plus } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SourceCard } from "@/components/source-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { UploadDialog } from "@/components/upload-dialog";
import type { Source, SourceKind } from "@/lib/types";
import { cn } from "@/lib/utils";

const FILTERS: { value: SourceKind | null; label: string }[] = [
  { value: null, label: "All" },
  { value: "trial", label: "Trials" },
  { value: "drug_label", label: "Labels" },
  { value: "guideline", label: "Guidelines" },
];

export function CorpusSidebar({
  sources,
  loading,
  error,
  scope,
  onScopeChange,
  onReload,
}: {
  sources: Source[];
  loading: boolean;
  error: string | null;
  scope: SourceKind | null;
  onScopeChange: (kind: SourceKind | null) => void;
  onReload: () => void;
}) {
  const [uploadOpen, setUploadOpen] = useState(false);
  const visible = scope ? sources.filter((s) => s.kind === scope) : sources;

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between gap-2 px-4 py-3">
        <div>
          <h2 className="flex items-center gap-1.5 text-sm font-semibold">
            <FileStack className="size-4 text-primary" />
            Corpus
          </h2>
          <p className="text-xs text-muted-foreground">
            {sources.length} document{sources.length === 1 ? "" : "s"}
          </p>
        </div>
        <Button size="sm" onClick={() => setUploadOpen(true)} className="gap-1.5">
          <Plus className="size-3.5" />
          Upload
        </Button>
      </div>

      <div className="flex gap-1 px-4 pb-3">
        {FILTERS.map((f) => (
          <button
            key={f.label}
            onClick={() => onScopeChange(f.value)}
            className={cn(
              "rounded-md px-2 py-1 text-xs font-medium transition-colors",
              scope === f.value
                ? "bg-primary/12 text-primary"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="scrollbar-thin flex-1 space-y-2 overflow-y-auto px-4 pb-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[4.5rem] w-full" />)
        ) : error ? (
          <EmptyState
            title="Couldn't load sources"
            description={error}
            action={
              <Button variant="outline" size="sm" onClick={onReload}>
                Retry
              </Button>
            }
          />
        ) : visible.length === 0 ? (
          <EmptyState
            title={sources.length === 0 ? "No documents yet" : "Nothing in this filter"}
            description={
              sources.length === 0
                ? "Upload a document to start asking grounded questions."
                : "Try a different document kind."
            }
          />
        ) : (
          visible.map((s) => <SourceCard key={s.id} source={s} />)
        )}
      </div>

      <UploadDialog open={uploadOpen} onClose={() => setUploadOpen(false)} onUploaded={onReload} />
    </div>
  );
}
