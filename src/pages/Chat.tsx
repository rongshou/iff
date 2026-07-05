import { useState, useRef, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import type { ChatMessage } from "../types";
import MessageBubble from "../components/MessageBubble";
import { SCENES } from "../config/scenes";
import type { SceneId } from "../config/scenes";
import { useChatInput } from "../hooks/useChatInput";
import { useChatScroll } from "../hooks/useChatScroll";
import { useChatSend } from "../hooks/useChatSend";
import { useChatStore } from "../store/chatStore";
type SceneState = Record<SceneId, ChatMessage[]>;

export default function ChatPage() {
  const { input, setInput, inputRef, handleKeyDown } = useChatInput(() => handleSend());
  const { scrollRef, showScrollBottom, setShowScrollBottom, onScroll, scrollToBottom } = useChatScroll();
  const [activeScene, setActiveScene] = useState<SceneId>("school");
  // 每个场景的对话历史独立存储，切换 Tab 不串
  const [scenes, setScenes] = useState<SceneState>(() => ({
    school: [],
    essay: [],
    visa: [],
  }));
  const loading = useChatStore((s) => s.loading);
  const error = useChatStore((s) => s.error);
  const collectedInfo = useChatStore((s) => s.collectedInfo);
  const setLoading = useChatStore((s) => s.setLoading as React.Dispatch<React.SetStateAction<boolean>>);
  const setError = useChatStore((s) => s.setError as React.Dispatch<React.SetStateAction<string | null>>);
  const setCollectedInfo = useChatStore((s) => s.setCollectedInfo);

  const abortRef = useRef<AbortController | null>(null);
  const atBottomRef = useRef(true);
  const { handleSend, handleStop, handleClear, handleClearAll } = useChatSend(
    activeScene, scenes, setScenes, collectedInfo, setCollectedInfo,
    setLoading, setError, setInput, inputRef, abortRef,
    loading, input, atBottomRef,
  );

  const messages = scenes[activeScene];
  const scene = useMemo(
    () => SCENES.find((s) => s.id === activeScene)!,
    [activeScene]
  );

  // 累计所有场景的消息数，用于顶部"清空"按钮的显示
  const totalMessages = Object.values(scenes).reduce(
    (n, arr) => n + arr.length,
    0
  );

  // 自动滚到底部（仅当用户已经在底部时）
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (atBottomRef.current) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [messages, loading]);

  // 切换 Tab 时重置滚动到底
  useEffect(() => {
    atBottomRef.current = true;
    setShowScrollBottom(false);
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "auto" });
  }, [activeScene]);

  // 输入框自动增高
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [input]);

  // ref 避免 onScroll 依赖 messages.length（频繁变化导致回调重建）
  const msgLenRef = useRef(0);
  msgLenRef.current = messages.length;

  // onScroll extracted to useChatScroll hook

  // scrollToBottom extracted to useChatScroll hook


  const handleRetry = () => {
    if (loading || messages.length === 0) return;
    const lastUserIdx = [...messages].reverse().findIndex((m) => m.role === "user");
    if (lastUserIdx === -1) return;
    const lastUser = messages[messages.length - 1 - lastUserIdx];
    const cut = messages.slice(0, messages.length - lastUserIdx);
    setScenes((prev) => ({ ...prev, [activeScene]: cut }));
    setError(null);
    setTimeout(() => handleSend(lastUser.content), 50);
  };

  const isEmpty = messages.length === 0;
  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
  const lastAssistantDone =
    lastAssistant && !loading && lastAssistant.content && !lastAssistant.content.startsWith("抱歉");

  return (
    <div className="h-screen chat-bg flex flex-col overflow-hidden">
      <div className="max-w-3xl w-full mx-auto flex-1 flex flex-col px-4 sm:px-6 py-4 sm:py-6">
        {/* ---------- 顶部标题栏 ---------- */}
        <header
          className={`flex items-center justify-between transition-all ${
            isEmpty ? "mb-4 sm:mb-5" : "mb-3 sm:mb-4"
          }`}
        >
          <div className="flex items-center gap-2 min-w-0">
            <span className="inline-block w-1 h-5 rounded-full bg-gradient-to-b from-indigo-500 to-purple-500 shrink-0" />
            <h1
              className={`font-bold text-slate-900 transition-all truncate ${
                isEmpty ? "text-xl sm:text-2xl" : "text-base sm:text-lg"
              }`}
            >
AI 留学智能问答
            </h1>
            <span className="hidden sm:inline text-slate-300">·</span>
            <span className="hidden sm:inline text-slate-500 text-sm truncate">
              {scene.label}
            </span>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <Link
              to="/"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium text-indigo-600 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 transition-all whitespace-nowrap"
              title="首页"
            >
              <span>🏠</span>
              <span>首页</span>
            </Link>
            <Link
              to="/profile"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium text-slate-400 border border-slate-200 hover:text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50 transition-all whitespace-nowrap"
              title="我的档案"
            >
              <span>📁</span>
              <span>档案</span>
            </Link>
            <a
              href="../tianshu/"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium text-slate-400 border border-slate-200 hover:text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50 transition-all whitespace-nowrap"
              title="切换到天枢测评"
            >
              <span>🧭</span>
              <span>天枢</span>
            </a>
            {totalMessages > 0 && (
              <>
                <button
                  onClick={handleClear}
                  className="text-xs sm:text-sm text-slate-500 hover:text-red-600 px-2.5 py-1.5 rounded-lg hover:bg-red-50 transition-colors flex items-center gap-1"
                  title="只清空当前场景的对话"
                >
                  <span className="text-sm leading-none">🗑</span>
                  <span className="hidden sm:inline">清空本场景</span>
                  <span className="sm:hidden">清空</span>
                </button>
                <button
                  onClick={handleClearAll}
                  className="text-xs sm:text-sm text-slate-400 hover:text-red-600 px-2.5 py-1.5 rounded-lg hover:bg-red-50 transition-colors"
                  title="清空所有对话"
                >
                  全部清空
                </button>
              </>
            )}
          </div>
        </header>

        {/* ---------- 场景 Tab ---------- */}
        <div className="mb-3 sm:mb-4 -mx-1 px-1 overflow-x-auto thin-scrollbar">
          <div className="inline-flex gap-1 p-1 bg-slate-100/80 rounded-xl">
            {SCENES.map((s) => {
              const isActive = activeScene === s.id;
              const count = scenes[s.id].length;
              return (
                <button
                  key={s.id}
                  onClick={() => setActiveScene(s.id)}
                  className={`relative flex items-center gap-1.5 px-3 sm:px-4 py-1.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                    isActive
                      ? "bg-white text-slate-900 shadow-sm"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <span className="text-base leading-none">{s.icon}</span>
                  <span>{s.shortLabel}</span>
                  {count > 0 && (
                    <span
                      className={`inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-semibold ${
                        isActive
                          ? "bg-indigo-100 text-indigo-700"
                          : "bg-slate-200 text-slate-600"
                      }`}
                    >
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* ---------- 主体区域 ---------- */}
        {isEmpty ? (
          <EmptyState
            scene={scene}
            onPick={(t) => {
              // 点击快捷问题：填到输入框，不直接发送，让用户自己修改后再发
              setInput(t);
              setTimeout(() => inputRef.current?.focus(), 0);
            }}
            onSceneChange={setActiveScene}
          />
        ) : (
          <div
            ref={scrollRef}
            onScroll={onScroll}
            className="flex-1 overflow-y-auto thin-scrollbar space-y-4 sm:space-y-5 pr-1 -mr-1 pb-2"
          >
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            {error && (
              <div className="flex justify-center">
                <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 border border-red-100 px-3 py-1.5 rounded-full">
                  <span>⚠ {error}</span>
                  <button
                    onClick={handleRetry}
                    className="underline hover:no-underline"
                  >
                    重试
                  </button>
                </div>
              </div>
            )}
            {lastAssistantDone && !loading && (
              <div className="flex flex-wrap gap-2 pl-11">
                {scene.followups.map((s) => (
                  <button
                    key={s}
                    onClick={() => {
                      // 追问建议：填到输入框，让用户修改后再发
                      setInput(s);
                      setTimeout(() => inputRef.current?.focus(), 0);
                    }}
                    className="text-xs px-3 py-1.5 rounded-full bg-white border border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50/50 transition-colors"
                  >
                    + {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 回到最新 */}
        {showScrollBottom && (
          <div className="flex justify-center -mt-2 mb-2 relative z-10">
            <button
              onClick={scrollToBottom}
              className="text-xs px-3 py-1.5 rounded-full bg-white border border-slate-200 shadow-md text-slate-600 hover:text-indigo-600 hover:border-indigo-300"
            >
              ↓ 回到最新
            </button>
          </div>
        )}

        {/* ---------- 输入区 ---------- */}
        <div className="mt-3 sm:mt-4">
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`聊聊${scene.label}相关的问题...（Enter 发送，Shift+Enter 换行）`}
              disabled={false}
              rows={1}
              className="w-full resize-none bg-transparent px-4 pt-3 pb-2 text-sm sm:text-[15px] text-slate-800 placeholder:text-slate-400 focus:outline-none disabled:opacity-60 max-h-40 thin-scrollbar"
            />
            <div className="flex items-center justify-between px-3 pb-3">
              <div className="text-[11px] text-slate-400 hidden sm:block">
                当前场景：{scene.label} · 内容仅供参考
              </div>
              <div className="flex items-center gap-2 ml-auto">
                {loading ? (
                  <button
                    onClick={handleStop}
                    className="px-4 py-2 rounded-xl text-sm font-medium bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors flex items-center gap-1.5"
                  >
                    <span className="w-2 h-2 bg-slate-500 rounded-sm" />
                    停止
                  </button>
                ) : (
                  <button
                    onClick={() => handleSend()}
                    disabled={!input.trim()}
                    className="btn-primary px-5 py-2 rounded-xl text-sm font-medium flex items-center gap-1.5"
                  >
                    发送
                    <span className="text-base leading-none">↑</span>
                  </button>
                )}
              </div>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 text-center sm:hidden">
            AI 回复仅供参考 · 切换 Tab 不会串上下文
          </p>
        </div>
      </div>
    </div>
  );
}

/* ---------- 空状态 ---------- */

import EmptyState from "../components/EmptyState";


/* ---------- 消息气泡已抽出为独立组件：src/components/MessageBubble.tsx ---------- */
