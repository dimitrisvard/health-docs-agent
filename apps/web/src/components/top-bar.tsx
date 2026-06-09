"use client";

import { Activity, PanelLeft } from "lucide-react";
import Link from "next/link";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button, buttonVariants } from "@/components/ui/button";

export function TopBar({ onToggleSidebar }: { onToggleSidebar: () => void }) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b bg-background/80 px-4 backdrop-blur">
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={onToggleSidebar}
          aria-label="Toggle corpus sidebar"
        >
          <PanelLeft />
        </Button>
        <span className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Activity className="size-4" />
          </span>
          Health Docs <span className="font-normal text-muted-foreground">Agent</span>
        </span>
      </div>
      <div className="flex items-center gap-2">
        <Link href="/evals" className={buttonVariants({ variant: "ghost", size: "sm" })}>
          Evals
        </Link>
        <span className="hidden items-center gap-1.5 rounded-full border border-primary/20 bg-primary/8 px-2.5 py-1 text-xs font-medium text-primary sm:inline-flex">
          Not medical advice
        </span>
        <ThemeToggle />
      </div>
    </header>
  );
}
