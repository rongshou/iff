import { useState, useRef, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import type { ChatMessage } from "../types";
import { sendChat, streamChat } from "../services/chat";
import { mergeChatInfo, createChatHistoryItem, addHistoryItem, loadProfile } from "../services/profile";
import MessageBubble from "../components/MessageBubble";
import { SCENES } from "../config/scenes";
import type { SceneId } from "../config/scenes";
import { generateId, ts, SCENE_INFO, looksLikeSchoolRequest, extractInfo, getMissingFields, profileToInfo, infoToDescription } from "../services/chat-helpers";
import { useChatInput } from "../hooks/useChatInput";
import { useChatScroll } from "../hooks/useChatScroll";
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  /** 已收集的信息（每个场景） */
  const [collectedInfo, setCollectedInfo] = useState<Record<string, Record<string, string>>>({});

  const abortRef = useRef<AbortController | null>(null);
  const atBottomRef = useRef(true);

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

  const handleStop = () => {
    abortRef.current?.abort();
    abortRef.current = null;
  };

  const updateSceneMessages = (updater: (prev: ChatMessage[]) => ChatMessage[]) => {
    setScenes((prev) => ({ ...prev, [activeScene]: updater(prev[activeScene]) }));
  };

  const handleSend = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || loading) return;
    setError(null);

    const userMsg: ChatMessage = {
      id: generateId(),
      role: "user",
      content,
      timestamp: ts(),
    };

    // 先把用户消息压入当前场景
    const updatedMessages = [...messages, userMsg];
    updateSceneMessages(() => updatedMessages);
    setInput("");
    setLoading(true);
    atBottomRef.current = true;

    // ---------- 信息收集检查（仅 school 场景且消息像是选校请求时才触发）----------
    const isSchoolRequest = activeScene === "school" && looksLikeSchoolRequest(content);
    if (isSchoolRequest) {
      const currentInfo = collectedInfo[activeScene] || {};
      const fields = SCENE_INFO[activeScene];

      // 首次进入: 从个人档案预填已有信息, 避免追问已设置的字段
      let baseInfo: Record<string, string> = {};
      if (!collectedInfo[activeScene] || Object.keys(currentInfo).length === 0) {
        const profile = loadProfile();
        if (profile) baseInfo = profileToInfo(profile);
      }

      const newInfo = { ...baseInfo, ...currentInfo, ...await extractInfo(content) };
      const missing = getMissingFields(newInfo, fields);

      // 首次且信息不全 → 逐个追问
      if (!collectedInfo[activeScene] && missing.length > 0) {
        const nextField = missing[0];
        setCollectedInfo((prev) => ({ ...prev, [activeScene]: newInfo }));
        updateSceneMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: "assistant",
            content: `收到您提供的信息，但还有一些不清楚的地方，需要跟您进一步确认：\n\n**${nextField.prompt}**\n\n提示：${nextField.hint}`,
            timestamp: ts(),
          },
        ]);
        setLoading(false);
        return;
      }

      // 追问后信息补充完整 → 整合发给 AI
      if (missing.length === 0 && !collectedInfo[activeScene]) {
        setCollectedInfo((prev) => ({ ...prev, [activeScene]: newInfo }));
        mergeChatInfo(newInfo); // 自动保存到个人档案
        const desc = infoToDescription(newInfo);
        const infoMsg: ChatMessage = {
          id: generateId(),
          role: "user" as const,
          content: `我提供的信息如下：\n${desc}\n\n请根据以上信息帮我分析。`,
          timestamp: ts(),
        };
        updateSceneMessages((prev) => [...prev.slice(0, -1), infoMsg]);
        const finalMessages = [...updatedMessages.slice(0, -1), infoMsg];
        await doSendToAI(finalMessages);
        return;
      }

      // 已有信息或非首次 → 正常调 AI（同时合并本轮新提取的字段）
      if (collectedInfo[activeScene] && Object.keys(collectedInfo[activeScene]).length > 0) {
        // 如果本轮消息提取出了新字段 → 更新状态并落盘
        const hasNewInfo = Object.keys(newInfo).length > Object.keys(currentInfo).length;
        if (hasNewInfo) {
          setCollectedInfo((prev) => ({ ...prev, [activeScene]: newInfo }));
          mergeChatInfo(newInfo);
        }
        const desc = infoToDescription(newInfo); // 使用最新合并后的信息
        const enrichedMsg: ChatMessage = {
          id: userMsg.id,
          role: "user",
          content: `${content}\n\n（已知信息：${desc}）`,
          timestamp: ts(),
        };
        updateSceneMessages((prev) => [...prev.slice(0, -1), enrichedMsg]);
        await doSendToAI([...updatedMessages.slice(0, -1), enrichedMsg]);
        return;
      }

      // School request but no collected info and no missing fields → directly to AI
      await doSendToAI(updatedMessages);
      return;
    }

    // ---------- 多轮追问: 信息收集未完成时继续追问（即使当前消息不像选校请求）----------
    if (activeScene === "school" && collectedInfo[activeScene]) {
      const currentInfo = collectedInfo[activeScene] || {};
      const fields = SCENE_INFO[activeScene];
      const newInfo = { ...currentInfo, ...await extractInfo(content) };
      const missing = getMissingFields(newInfo, fields);

      if (missing.length > 0) {
        const nextField = missing[0];
        setCollectedInfo((prev) => ({ ...prev, [activeScene]: newInfo }));
        updateSceneMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: "assistant",
            content: `好的，还差最后几项：\n\n**${nextField.prompt}**\n\n提示：${nextField.hint}`,
            timestamp: ts(),
          },
        ]);
        setLoading(false);
        return;
      }

      // 所有字段收集完毕 → 整合发送
      setCollectedInfo((prev) => ({ ...prev, [activeScene]: newInfo }));
      mergeChatInfo(newInfo);
      const desc = infoToDescription(newInfo);
      updateSceneMessages((prev) => [
        ...prev.slice(0, -1),
        {
          id: userMsg.id,
          role: "user" as const,
          content: `我提供的信息如下：\n${desc}\n\n请根据以上信息帮我分析。`,
          timestamp: ts(),
        },
      ]);
      await doSendToAI([
        ...updatedMessages.slice(0, -1),
        { id: userMsg.id, role: "user" as const, content: `我提供的信息如下：\n${desc}\n\n请根据以上信息帮我分析。`, timestamp: ts() },
      ]);
      return;
    }

    // ---------- 非选校请求 → 直接调 AI ----------
    await doSendToAI(updatedMessages);
  };

  /** 调 AI（流式 + fallback） */
  const doSendToAI = async (msgs: ChatMessage[]) => {
    const assistantId = generateId();
    updateSceneMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "", timestamp: ts() },
    ]);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const apiMessages = msgs.map((m) => ({
        role: m.role as "user" | "assistant",
        content: m.content,
      }));

      let accumulated = "";
      let reasoningText = "";
      await streamChat(
        apiMessages,
        (chunk) => {
          accumulated += chunk;
          const current = accumulated;
          setScenes((prev) => ({
            ...prev,
            [activeScene]: prev[activeScene].map((m) =>
              m.id === assistantId ? { ...m, content: current } : m
            ),
          }));
        },
        () => {},
        controller.signal,
        (reasoning) => {
          reasoningText += reasoning;
          setScenes((prev) => ({
            ...prev,
            [activeScene]: prev[activeScene].map((m) =>
              m.id === assistantId ? { ...m, reasoning: reasoningText } : m
            ),
          }));
        }
      );
    } catch (e: any) {
      if (e?.name === "AbortError") {
        setScenes((prev) => ({
          ...prev,
          [activeScene]: prev[activeScene].map((m) =>
            m.id === assistantId && !m.content
              ? { ...m, content: "_（已停止生成）_" }
              : m
          ),
        }));
      } else {
        try {
          const apiMessages = msgs.map((m) => ({
            role: m.role as "user" | "assistant",
            content: m.content,
          }));
          const res = await sendChat(apiMessages);
          setScenes((prev) => ({
            ...prev,
            [activeScene]: prev[activeScene].map((m) =>
              m.id === assistantId ? { ...m, content: res.reply } : m
            ),
          }));
        } catch (retryErr: any) {
          const msg = retryErr?.message || "";
          let errorMsg = "网络异常，请稍后重试";
          let contentMsg = "抱歉，请求失败，请稍后重试。";
          if (msg.includes("401") || msg.includes("余额")) {
            errorMsg = "AI 服务暂不可用（余额不足），请联系管理员";
            contentMsg = "AI 服务暂不可用，请联系管理员处理。";
          } else if (msg.includes("500")) {
            errorMsg = "服务端处理出错，已记录日志，请稍后重试";
          } else if (msg.includes("timeout") || msg.includes("超时")) {
            errorMsg = "请求超时，请稍后重试";
          } else if (msg.includes("429") || msg.includes("Too Many Requests")) {
            errorMsg = "请求过于频繁，请稍后再试";
          }
          setError(errorMsg);
          setScenes((prev) => ({
            ...prev,
            [activeScene]: prev[activeScene].map((m) =>
              m.id === assistantId && !m.content
                ? { ...m, content: contentMsg }
                : m
            ),
          }));
        }
      }
    } finally {
      setLoading(false);
      abortRef.current = null;
      inputRef.current?.focus();
    }
  };



  const handleClear = () => {
    if (loading) handleStop();
    // 清空前把当前会话保存到历史
    if (messages.length >= 2) {
      addHistoryItem(createChatHistoryItem(activeScene, messages));
    }
    setScenes((prev) => ({ ...prev, [activeScene]: [] }));
    setCollectedInfo((prev) => ({ ...prev, [activeScene]: {} }));
    setError(null);
    setInput("");
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleClearAll = () => {
    if (loading) handleStop();
    if (!window.confirm("清空所有对话历史？此操作不可恢复。")) return;
    // 清空前保存所有非空会话
    for (const [sid, msgs] of Object.entries(scenes)) {
      if (msgs.length >= 2) {
        addHistoryItem(createChatHistoryItem(sid, msgs));
      }
    }
    setScenes({ school: [], essay: [], visa: [] });
    setCollectedInfo({});
    setError(null);
    setInput("");
  };

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
    <div className="min-h-screen chat-bg flex flex-col">
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
