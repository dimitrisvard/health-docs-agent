"use client";

import { BarChart3 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { EvalDashboard } from "@/components/eval-dashboard";
import { EmptyState } from "@/components/empty-state";
import { ThemeToggle } from "@/components/theme-toggle";
import { buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchEvals } from "@/lib/api";
import type { EvalReport } from "@/lib/types";

export default function EvalsPage() {
  const [report, setReport] = useState<EvalReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEvals()
      .then(setReport)
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex h-dvh flex-col">
      <header className="flex h-14 shrink-0 items-center justify-between border-b bg-background/80 px-4 backdrop-blur">
        <span className="flex items-center gap-2 font-semibold tracking-tight">
          <BarChart3 className="size-4 text-primary" />
          Evals
        </span>
        <div className="flex items-center gap-2">
          <Link href="/" className={buttonVariants({ variant: "outline", size: "sm" })}>
            Back to chat
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-6 py-8">
          {loading ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-20" />
                ))}
              </div>
              <Skeleton className="h-48" />
            </div>
          ) : error ? (
            <EmptyState
              icon={<BarChart3 className="size-5" />}
              title="Couldn't load evals"
              description={error}
            />
          ) : !report ? (
            <EmptyState
              icon={<BarChart3 className="size-5" />}
              title="No eval runs yet"
              description="Run make eval against a seeded corpus to populate retrieval and faithfulness metrics."
            />
          ) : (
            <EvalDashboard report={report} />
          )}
        </div>
      </main>
    </div>
  );
}
