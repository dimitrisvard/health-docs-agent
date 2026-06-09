import { BarChart3 } from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/empty-state";
import { buttonVariants } from "@/components/ui/button";

export default function EvalsPage() {
  return (
    <div className="flex h-dvh items-center justify-center p-6">
      <EmptyState
        icon={<BarChart3 className="size-5" />}
        title="Evals dashboard"
        description="Retrieval and faithfulness metrics from the latest eval run will render here. Wired up in Phase 5 — run make eval to populate."
        action={
          <Link href="/" className={buttonVariants({ variant: "outline", size: "sm" })}>
            Back to chat
          </Link>
        }
      />
    </div>
  );
}
