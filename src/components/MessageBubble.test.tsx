import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MessageBubble from "./MessageBubble";
import type { ChatMessage } from "../types";

// fixed epoch ms for deterministic time formatting
const USER_TS = new Date("2026-06-30T12:00:00").getTime();
const ASSISTANT_TS = new Date("2026-06-30T12:01:00").getTime();

const userMsg: ChatMessage = {
  id: "1",
  role: "user",
  content: "Hello from user",
  timestamp: USER_TS,
};

const assistantMsg: ChatMessage = {
  id: "2",
  role: "assistant",
  content: "Hello from assistant",
  timestamp: ASSISTANT_TS,
};

describe("MessageBubble", () => {
  it("renders user message content", () => {
    render(<MessageBubble msg={userMsg} />);
    expect(screen.getByText("Hello from user")).toBeDefined();
  });

  it("renders assistant message content", () => {
    render(<MessageBubble msg={assistantMsg} />);
    expect(screen.getByText("Hello from assistant")).toBeDefined();
  });

  it("renders formatted timestamp for user", () => {
    render(<MessageBubble msg={userMsg} />);
    // formatTime uses local hours/minutes; using local TZ-aware matcher
    const d = new Date(USER_TS);
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    expect(screen.getByText(`${hh}:${mm}`)).toBeDefined();
  });
});
