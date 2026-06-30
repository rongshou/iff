import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import PathwaySection from "./PathwaySection";
import type { PathwaySuggestion } from "../types";

const suggestions: PathwaySuggestion[] = [
  {
    university: "Test University",
    country: "US",
    qs_rank: 50,
    usnews_rank: 30,
    programs: [
      {
        name: "Master's Preparation",
        duration: "1 year",
        fee_range: "$30,000-$40,000",
        entry_requirement: "GPA 2.5+",
      },
    ],
  },
];

describe("PathwaySection", () => {
  it("renders nothing when suggestions is empty", () => {
    const { container } = render(<PathwaySection suggestions={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders university name", () => {
    render(<PathwaySection suggestions={suggestions} />);
    expect(screen.getByText("Test University")).toBeDefined();
  });

  it("renders country flag", () => {
    render(<PathwaySection suggestions={suggestions} />);
    expect(screen.getByText("🇺🇸")).toBeDefined();
  });

  it("renders program duration", () => {
    render(<PathwaySection suggestions={suggestions} />);
    expect(screen.getByText((t) => t.includes("1 year"))).toBeDefined();
  });

  it("renders pathway section header", () => {
    render(<PathwaySection suggestions={suggestions} />);
    expect(screen.getByText("预科/通路建议")).toBeDefined();
  });
});
