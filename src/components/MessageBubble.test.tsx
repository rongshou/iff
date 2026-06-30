import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MessageBubble from "./MessageBubble";
import type { ChatMessage } from "../types";

const userMsg: ChatMessage = {
  id: "1",
  role: "user",
  content: "Hello from user",
  timestamp: "12:00",
};

const assistantMsg: ChatMessage = {
  id: "2",
  role: "assistant",
  content: "Hello from assistant",
  timestamp: "12:01",
};

describe("MessageBubble", () => {
  it("renders user message", () => {
    render(<MessageBubble msg={userMsg} />);
    expect(screen.getByText("Hello from user")).toBeDefined();
  });

  it("renders assistant message", () => {
    render(<MessageBubble msg={assistantMsg} />);
    expect(screen.getByText("Hello from assistant")).toBeDefined();
  });
});
