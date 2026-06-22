const API_BASE = "/tianquan-api";

export interface ChatMessageInput {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
  messages: ChatMessageInput[];
}

export async function sendChat(
  messages: ChatMessageInput[],
  stream: boolean = false
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, stream }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "请求失败");
  }
  return res.json();
}

export async function streamChat(
  messages: ChatMessageInput[],
  onChunk: (text: string) => void,
  onDone: () => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, stream: true }),
    signal,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "请求失败");
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("无法读取流式响应");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    if (signal?.aborted) {
      try { await reader.cancel(); } catch { /* ignore */ }
      throw Object.assign(new Error("aborted"), { name: "AbortError" });
    }
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6).trim();
        if (data === "[DONE]") {
          onDone();
          return;
        }
        try {
          const obj = JSON.parse(data);
          if (obj.content) onChunk(obj.content);
        } catch {
          // skip invalid JSON
        }
      }
    }
  }
  onDone();
}