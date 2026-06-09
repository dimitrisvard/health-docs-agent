import type { Citation } from "@/lib/types";
import { cn } from "@/lib/utils";

export function CitationChips({
  citations,
  className,
}: {
  citations: Citation[];
  className?: string;
}) {
  if (citations.length === 0) return null;

  return (
    <div className={cn("flex flex-wrap gap-1.5", className)}>
      {citations.map((c) => (
        <span
          key={c.id}
          title={c.text ?? undefined}
          className="inline-flex max-w-[16rem] items-center gap-1 rounded-md border bg-muted/50 px-2 py-0.5 text-xs text-muted-foreground"
        >
          <span className="font-mono text-[10px] text-primary">#{c.id}</span>
          <span className="truncate">
            {c.title}
            {c.section ? ` · ${c.section}` : ""}
          </span>
        </span>
      ))}
    </div>
  );
}
