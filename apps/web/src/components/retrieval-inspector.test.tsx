import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RetrievalInspector } from "@/components/retrieval-inspector";
import type { Citation } from "@/lib/types";

const citations: Citation[] = [
  {
    id: 1,
    document_id: 7,
    title: "Drug X SmPC",
    section: "Contraindications",
    score: 0.031,
    text: "Do not use in pregnancy.",
  },
];

describe("RetrievalInspector", () => {
  it("summarises the fired tool and chunk count, then expands to show both", () => {
    render(<RetrievalInspector citations={citations} tools={["mcp__retrieval__hybrid_search"]} />);

    const toggle = screen.getByRole("button");
    expect(toggle).toHaveTextContent("hybrid_search"); // prefix stripped
    expect(toggle).toHaveTextContent("1 chunks");

    fireEvent.click(toggle);
    expect(screen.getByText("Do not use in pregnancy.")).toBeInTheDocument();
  });

  it("renders nothing without tools or chunks", () => {
    const { container } = render(<RetrievalInspector citations={[]} tools={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});
