import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CitationChips } from "@/components/citation-chips";
import type { Citation } from "@/lib/types";

const citations: Citation[] = [
  {
    id: 12,
    document_id: 3,
    title: "Drug X SmPC",
    section: "Contraindications",
    score: 0.031,
    text: "Do not use in pregnancy.",
  },
];

describe("CitationChips", () => {
  it("renders a chip with the chunk id and source", () => {
    render(<CitationChips citations={citations} />);
    expect(screen.getByText("#12")).toBeInTheDocument();
    expect(screen.getByText(/^Drug X SmPC · Contraindications$/)).toBeInTheDocument();
  });

  it("renders nothing when there are no citations", () => {
    const { container } = render(<CitationChips citations={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});
