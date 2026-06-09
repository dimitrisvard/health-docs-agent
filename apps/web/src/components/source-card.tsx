import { Badge } from "@/components/ui/badge";
import { KIND_LABEL, type Source } from "@/lib/types";

export function SourceCard({ source }: { source: Source }) {
  return (
    <div className="rounded-lg border bg-card p-3 transition-colors hover:border-primary/30">
      <h3 className="text-sm font-medium leading-snug">{source.title}</h3>
      <div className="mt-2 flex items-center justify-between gap-2">
        <Badge variant={source.kind}>{KIND_LABEL[source.kind]}</Badge>
        {source.source_uri && (
          <a
            href={source.source_uri}
            target="_blank"
            rel="noreferrer"
            className="truncate text-xs text-muted-foreground hover:text-primary"
          >
            source
          </a>
        )}
      </div>
    </div>
  );
}
