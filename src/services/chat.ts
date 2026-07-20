import { getAuthHeaders } from "./auth";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

/** 每次对话保存到后端 */
export async function saveChatTurn(
  session_id: string,
  scene: string,
  user_message: string,
  assistant_message: string,
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/chat/history`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({ session_id, scene, user_message, assistant_message }),
    });
    const data = await res.json();
    return data.ok === true;
  } catch (e) {
    console.warn("saveChatTurn failed:", e);
    return false;
  }
}

/** 从后端获取对话历史 */
export async function fetchChatHistory(
  limit: number = 100,
  offset: number = 0,
): Promise<{ sessions: any[]; total: number }> {
  try {
    const res = await fetch(`${API_BASE}/chat/history?limit=${limit}&offset=${offset}`, {
      headers: { ...getAuthHeaders() },
    });
    return await res.json();
  } catch (e) {
    console.warn("fetchChatHistory failed:", e);
    return { sessions: [], total: 0 };
  }
}

/** 删除后端对话历史 */
export async function deleteChatHistory(session_id?: string): Promise<boolean> {
  try {
    const url = session_id
      ? `${API_BASE}/chat/history?session_id=${encodeURIComponent(session_id)}`
      : `${API_BASE}/chat/history`;
    const res = await fetch(url, {
      method: "DELETE",
      headers: { ...getAuthHeaders() },
    });
    const data = await res.json();
    return data.ok === true;
  } catch (e) {
    console.warn("deleteChatHistory failed:", e);
    return false;
  }
}

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
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({ messages, stream }),
    });
  } catch {
    throw new Error("网络连接失败，请检查网络后重试");
  }
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
  signal?: AbortSignal,
  onReasoning?: (text: string) => void
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({ messages, stream: true }),
      signal,
    });
  } catch (e: any) {
    if (signal?.aborted) {
      throw Object.assign(new Error("aborted"), { name: "AbortError" });
    }
    throw new Error("网络连接失败，请检查网络后重试");
  }
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
          if (obj.reasoning && onReasoning) onReasoning(obj.reasoning);
        } catch {
          // skip invalid JSON
        }
      }
    }
  }

  // Flush decoder and process any remaining content in the buffer
  buffer += decoder.decode();
  if (buffer.trim()) {
    const lines = buffer.split("\n");
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
          if (obj.reasoning && onReasoning) onReasoning(obj.reasoning);
        } catch {
          // skip invalid JSON
        }
      }
    }
  }

  onDone();
}