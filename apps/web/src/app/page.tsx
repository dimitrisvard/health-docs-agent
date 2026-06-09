"use client";

import { useCallback, useEffect, useState } from "react";

import { ChatPanel } from "@/components/chat-panel";
import { CorpusSidebar } from "@/components/corpus-sidebar";
import { TopBar } from "@/components/top-bar";
import { fetchSources } from "@/lib/api";
import type { Source, SourceKind } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function Home() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scope, setScope] = useState<SourceKind | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setSources(await fetchSources());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="flex h-dvh flex-col">
      <TopBar onToggleSidebar={() => setSidebarOpen((v) => !v)} />
      <div className="relative flex min-h-0 flex-1">
        <aside
          className={cn(
            "z-40 w-72 shrink-0 border-r bg-background",
            "max-lg:absolute max-lg:inset-y-0 max-lg:left-0 max-lg:shadow-xl max-lg:transition-transform",
            sidebarOpen ? "max-lg:translate-x-0" : "max-lg:-translate-x-full",
          )}
        >
          <CorpusSidebar
            sources={sources}
            loading={loading}
            error={error}
            scope={scope}
            onScopeChange={(k) => {
              setScope(k);
              setSidebarOpen(false);
            }}
            onReload={load}
          />
        </aside>

        {sidebarOpen && (
          <div
            className="absolute inset-0 z-30 bg-foreground/20 lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
        )}

        <main className="min-w-0 flex-1">
          <ChatPanel scope={scope} />
        </main>
      </div>
    </div>
  );
}
