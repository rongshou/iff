import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import EmptyState from "./EmptyState";
import type { Scene } from "../config/scenes";

const testScene: Scene = {
  id: "school",
  label: "选校定位",
  shortLabel: "选校",
  icon: "🎓",
  greeting: "选校定位 · 我来帮你参谋",
  intro: "test intro",
  quickPrompts: [{ icon: "🇬🇧", text: "Test prompt" }],
  followups: ["Test followup"],
};

describe("EmptyState", () => {
  it("does not render scene hint", () => {
    render(<EmptyState scene={testScene} onPick={vi.fn()} onSceneChange={vi.fn()} />);
    // hint 行已删除，不应出现任何 hint 文字
    expect(screen.queryByText("PS / CV / 推荐信")).toBeNull();
    expect(screen.queryByText("F-1 / Tier 4 / 材料清单")).toBeNull();
  });

  it("renders quick prompts", () => {
    render(<EmptyState scene={testScene} onPick={vi.fn()} onSceneChange={vi.fn()} />);
    expect(screen.getByText("Test prompt")).toBeDefined();
  });
});
