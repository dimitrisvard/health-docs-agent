import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EvalDashboard } from "@/components/eval-dashboard";
import type { EvalReport } from "@/lib/types";

const report: EvalReport = {
  run: { id: 3, commit_sha: "abc1234def", created_at: "2026-06-09T00:00:00" },
  aggregates: { hit_at_5: 0.8, mrr: 0.7, ndcg: 0.75, faithfulness: 0.92 },
  results: [
    { question: "What are the contraindications?", hit_at_k: true, mrr: 1.0, ndcg: 1.0, faithfulness: 0.95 },
    { question: "Dosing in renal impairment?", hit_at_k: false, mrr: 0.0, ndcg: 0.0, faithfulness: null },
  ],
};

describe("EvalDashboard", () => {
  it("renders aggregate metric cards as percentages and decimals", () => {
    render(<EvalDashboard report={report} />);
    expect(screen.getByText("80%")).toBeInTheDocument(); // hit@5
    expect(screen.getByText("92%")).toBeInTheDocument(); // faithfulness
    expect(screen.getByText("0.700")).toBeInTheDocument(); // mrr
  });

  it("renders a row per question with hit/miss badges", () => {
    render(<EvalDashboard report={report} />);
    expect(screen.getByText("What are the contraindications?")).toBeInTheDocument();
    expect(screen.getByText("hit")).toBeInTheDocument();
    expect(screen.getByText("miss")).toBeInTheDocument();
  });
});
