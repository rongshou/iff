import { useState, useMemo, memo } from "react";
import type { ChatMessage } from "../types";
import { renderMarkdown } from "../utils/markdown";

function formatTime(ms: number) {
  const d = new Date(ms);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

/* ---------- 子组件 ---------- */

function Avatar({ role }: { role: "user" | "assistant" }) {
  if (role === "user") {
    return (
      <div className="shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white grid place-items-center text-sm font-semibold shadow-sm">
        我
      </div>
    );
  }
  return (
    <div className="shrink-0 w-9 h-9 rounded-full bg-white border border-slate-200 grid place-items-center shadow-sm">
      <span className="text-base brand-gradient font-bold">天</span>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  };
  return (
    <button
      onClick={onCopy}
      className="opacity-0 group-hover:opacity-100 transition-opacity text-xs px-2 py-1 rounded-md text-slate-500 hover:text-indigo-600 hover:bg-indigo-50"
      aria-label="复制"
    >
      {copied ? "✓ 已复制" : "📋 复制"}
    </button>
  );
}

function TypingDots() {
  return (
    <span className="dot-bounce inline-flex items-center" aria-label="正在输入">
      <span /><span /><span />
    </span>
  );
}

/* ---------- 消息气泡（React.memo 避免无关消息重渲染） ---------- */

const MessageBubble = memo(function MessageBubble({ msg, loading }: { msg: ChatMessage; loading?: boolean }) {
  const isUser = msg.role === "user";
  const isStreaming = !!loading && !isUser && !!msg.content;
  // Skip expensive markdown rendering while streaming — render raw text via CSS instead.
  // renderMarkdown is O(n) and was being called on EVERY token (500-2000x per response),
  // saturating the main thread and freezing the page.
  const renderedContent = useMemo(() => {
    if (!msg.content) return null;
    if (isStreaming) return null; // will render raw text below
    return renderMarkdown(msg.content);
  }, [msg.content, isStreaming]);

  return (
    <div className={`flex flex-col gap-1.5 ${isUser ? "items-end" : "items-start"}`}>
      <Avatar role={msg.role} />
      <div
        className={`group flex flex-col ${
          isUser ? "items-end" : "items-start"
        } max-w-[85%] sm:max-w-[75%]`}
      >
        <div
          className={`bubble-shadow ${
            isUser
              ? "bubble-user px-4 py-2.5 rounded-2xl rounded-tr-md"
              : "bubble-ai px-[18px] py-3.5 rounded-2xl rounded-tl-md"
          } text-[15px] sm:text-[15.5px] leading-relaxed ${
            isUser ? "" : "prose-chat"
          }`}
        >
          {isUser ? (
            <div className="whitespace-pre-wrap break-words">{msg.content}</div>
          ) : msg.content ? (
            isStreaming ? (
              <div className="whitespace-pre-wrap break-words">{msg.content}</div>
            ) : (
              <div className="break-words">{renderedContent}</div>
            )
          ) : msg.reasoning ? (
            <div className="flex items-center gap-2 text-slate-400 text-[13px]">
              <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                <path className="opacity-80" d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
              </svg>
              <span>正在思考…</span>
            </div>
          ) : (
            <TypingDots />
          )}
        </div>
        <div
          className={`flex items-center gap-2 mt-0.5 px-1 ${isUser ? "flex-row-reverse" : "flex-row"}`}
        >
          <span className="text-[10px] text-slate-400">
            {formatTime(msg.timestamp)}
          </span>
          {!isUser && msg.content && <CopyButton text={msg.content} />}
        </div>
      </div>
    </div>
  );
}, (prev, next) => prev.msg.id === next.msg.id && prev.msg.content === next.msg.content && prev.msg.reasoning === next.msg.reasoning && prev.loading === next.loading);

export default MessageBubble;