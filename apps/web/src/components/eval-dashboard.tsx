import type { EvalAggregates, EvalReport } from "@/lib/types";
import { cn } from "@/lib/utils";

function pct(value: number | null): string {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

function num(value: number | null): string {
  return value === null ? "—" : value.toFixed(3);
}

const CARDS: { key: keyof EvalAggregates; label: string; fmt: (v: number | null) => string }[] = [
  { key: "hit_at_5", label: "Hit@5", fmt: pct },
  { key: "mrr", label: "MRR", fmt: num },
  { key: "ndcg", label: "nDCG", fmt: num },
  { key: "faithfulness", label: "Faithfulness", fmt: pct },
];

export function EvalDashboard({ report }: { report: EvalReport }) {
  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">
        Run #{report.run.id}
        {report.run.created_at ? ` · ${new Date(report.run.created_at).toLocaleString()}` : ""}
        {report.run.commit_sha ? ` · ${report.run.commit_sha.slice(0, 7)}` : ""}
      </p>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {CARDS.map((card) => (
          <div key={card.key} className="rounded-xl border bg-card p-4 shadow-sm">
            <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {card.label}
            </div>
            <div className="mt-1 text-2xl font-semibold tabular-nums">
              {card.fmt(report.aggregates[card.key])}
            </div>
          </div>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-2 font-medium">Question</th>
              <th className="px-3 py-2 font-medium">Hit@5</th>
              <th className="px-3 py-2 font-medium">MRR</th>
              <th className="px-3 py-2 font-medium">nDCG</th>
              <th className="px-3 py-2 font-medium">Faith.</th>
            </tr>
          </thead>
          <tbody>
            {report.results.map((row, i) => (
              <tr key={i} className="border-t">
                <td className="px-4 py-2">{row.question}</td>
                <td className="px-3 py-2">
                  <HitBadge value={row.hit_at_k} />
                </td>
                <td className="px-3 py-2 tabular-nums text-muted-foreground">{num(row.mrr)}</td>
                <td className="px-3 py-2 tabular-nums text-muted-foreground">{num(row.ndcg)}</td>
                <td className="px-3 py-2 tabular-nums text-muted-foreground">{pct(row.faithfulness)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function HitBadge({ value }: { value: boolean | null }) {
  if (value === null) return <span className="text-muted-foreground">—</span>;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-medium",
        value ? "bg-primary/12 text-primary" : "bg-destructive/12 text-destructive",
      )}
    >
      {value ? "hit" : "miss"}
    </span>
  );
}
