import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import type { ChatMessage } from "../types";
import { sendChat, streamChat } from "../services/chat";
import { renderMarkdown } from "../utils/markdown";

/* =========================================================================
 * 场景（Tab）定义
 * 把留学问答拆成 4 个独立场景：每个场景有独立的对话历史 & 独立的开场白，
 * 避免 AI 在不同主题间串台（比如聊完选校去问签证，AI 还在选校语境里）。
 * ========================================================================= */

type SceneId = "school" | "essay" | "visa" | "career";

interface Scene {
  id: SceneId;
  label: string;
  icon: string;
  shortLabel: string;
  greeting: string;
  intro: string;
  quickPrompts: { icon: string; text: string }[];
  followups: string[];
}

const SCENES: Scene[] = [
  {
    id: "school",
    label: "选校定位",
    shortLabel: "选校",
    icon: "🎓",
    greeting: "选校定位 · 我来帮你定校",
    intro: "告诉我你的 GPA、学校、专业和目标，我会给你冲刺 / 主申 / 保底三档方案。",
    quickPrompts: [
      { icon: "🇬🇧", text: "英国硕士选校：北京邮电大学 通信工程 82/100 大三" },
      { icon: "🇺🇸", text: "美国 CS 硕士：985 计算机 GPA 3.4/4.0 已毕业" },
      { icon: "🇦🇺", text: "双非金融 85/100 大四，澳洲八大有机会吗？" },
      { icon: "📋", text: "先帮我评估选校，一步步问我的情况" },
    ],
    followups: [
      "推荐几所保底院校",
      "雅思/托福要考到多少？",
      "如何写一份有竞争力的 PS？",
    ],
  },
  {
    id: "essay",
    label: "文书写作",
    shortLabel: "文书",
    icon: "✍️",
    greeting: "文书写作 · 把故事讲好",
    intro: "PS / CV / 推荐信怎么开头？结构怎么排？亮点怎么挖？我可以给你思路与模板。",
    quickPrompts: [
      { icon: "📝", text: "我的 PS 第一段该怎么写？有什么开头模板？" },
      { icon: "📄", text: "帮我优化这段个人陈述：" },
      { icon: "📚", text: "推荐信应该找什么样的老师写？" },
      { icon: "🎯", text: "CV 怎么突出科研和项目经历？" },
    ],
    followups: [
      "PS 字数一般多少合适？",
      "如何把跨专业经历写成亮点？",
      "推荐信里要不要写缺点？",
    ],
  },
  {
    id: "visa",
    label: "签证与材料",
    shortLabel: "签证",
    icon: "🛂",
    greeting: "签证材料 · 一次过签",
    intro: "F-1 / Tier 4 / 资金证明 / 面签准备，材料清单和流程都帮你梳理清楚。",
    quickPrompts: [
      { icon: "🇺🇸", text: "F-1 签证需要准备哪些材料？" },
      { icon: "🇬🇧", text: "英国学生签资金证明要存多久？" },
      { icon: "💰", text: "签证存款多少合适？冻结期怎么算？" },
      { icon: "🎤", text: "美国签证面签常问哪些问题？" },
    ],
    followups: [
      "签证最早什么时候办？",
      "面签被拒了还能再签吗？",
      "I-20 是什么？怎么用？",
    ],
  },
  {
    id: "career",
    label: "求职与生活",
    shortLabel: "求职",
    icon: "💼",
    greeting: "求职生活 · 早做规划",
    intro: "OPT / PSW / 实习 / 校招 / 租房，提前布局，毕业才不会手忙脚乱。",
    quickPrompts: [
      { icon: "🇺🇸", text: "OPT 怎么申请？什么时候开始准备？" },
      { icon: "🇬🇧", text: "英国 PSW 签证能工作多久？" },
      { icon: "🏠", text: "伦敦/纽约租房大概多少钱？哪里性价比高？" },
      { icon: "📅", text: "留学生校招时间线是怎样的？" },
    ],
    followups: [
      "OPT 和 CPT 有什么区别？",
      "留学生怎么找第一份实习？",
      "毕业后留美难度大吗？",
    ],
  },
];

/* ---------- 工具函数 ---------- */

function generateId() {
  return Math.random().toString(36).slice(2, 10);
}

const ts = () => Date.now();

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

/* =========================================================================
 * 主组件
 * ========================================================================= */

type SceneState = Record<SceneId, ChatMessage[]>;

export default function ChatPage() {
  const [activeScene, setActiveScene] = useState<SceneId>("school");
  // 每个场景的对话历史独立存储，切换 Tab 不串
  const [scenes, setScenes] = useState<SceneState>(() => ({
    school: [],
    essay: [],
    visa: [],
    career: [],
  }));
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
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

  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    const atBottom = distance < 80;
    atBottomRef.current = atBottom;
    setShowScrollBottom(!atBottom && messages.length > 0);
  }, [messages.length]);

  const scrollToBottom = () => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    atBottomRef.current = true;
    setShowScrollBottom(false);
  };

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

    const assistantId = generateId();
    updateSceneMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "", timestamp: ts() },
    ]);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const apiMessages = updatedMessages.map((m) => ({
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
          const apiMessages = updatedMessages.map((m) => ({
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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    if (loading) handleStop();
    setScenes((prev) => ({ ...prev, [activeScene]: [] }));
    setError(null);
    setInput("");
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleClearAll = () => {
    if (loading) handleStop();
    if (!window.confirm("清空所有 4 个场景的对话历史？此操作不可恢复。")) return;
    setScenes({ school: [], essay: [], visa: [], career: [] });
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
              留学问答
            </h1>
            <span className="hidden sm:inline text-slate-300">·</span>
            <span className="hidden sm:inline text-slate-500 text-sm truncate">
              {scene.label}
            </span>
          </div>
          {totalMessages > 0 && (
            <div className="flex items-center gap-1 shrink-0">
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
                title="清空所有 4 个场景的对话"
              >
                全部清空
              </button>
            </div>
          )}
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

function EmptyState({
  scene,
  onPick,
  onSceneChange,
}: {
  scene: Scene;
  onPick: (t: string) => void;
  onSceneChange: (id: SceneId) => void;
}) {
  return (
    <div className="flex-1 flex flex-col justify-center">
      {/* Hero */}
      <div className="text-center mb-6 sm:mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white text-2xl sm:text-3xl font-bold shadow-lg shadow-indigo-200 mb-4">
          {scene.icon}
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2">
          {scene.greeting}
        </h2>
        <p className="text-slate-500 text-sm sm:text-base max-w-md mx-auto leading-relaxed">
          {scene.intro}
        </p>
      </div>

      {/* 使用说明 */}
      {scene.id === "school" && (
        <div className="mx-auto max-w-xl w-full mb-5 bg-indigo-50/70 border border-indigo-100 rounded-xl px-4 py-3 text-sm text-slate-700 leading-relaxed">
          <div className="font-semibold text-indigo-800 mb-1">💡 使用说明</div>
          <p>告诉我你的 GPA、学校、专业和目标国家，我会为你匹配真实案例，生成冲刺/主申/保底选校方案。也可以直接点击下方快捷问题开始 👇</p>
        </div>
      )}

      {/* 场景入口提示 */}
      <div className="text-center mb-5">
        <div className="inline-flex flex-wrap items-center justify-center gap-1 text-xs text-slate-400">
          <span>也可以聊聊</span>
          {SCENES.filter((s) => s.id !== scene.id).map((s, i, arr) => (
            <span key={s.id}>
              <button
                onClick={() => onSceneChange(s.id)}
                className="text-indigo-600 hover:underline font-medium"
              >
                {s.label}
              </button>
              {i < arr.length - 1 && <span className="mx-0.5">·</span>}
            </span>
          ))}
        </div>
      </div>

      {/* 快捷问题 —— 点击填到输入框（不直接发送），让用户自己修改后再发 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl mx-auto w-full">
        {scene.quickPrompts.map((p) => (
          <button
            key={p.text}
            onClick={() => onPick(p.text)}
            className="lift text-left px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 flex items-start gap-2 group"
          >
            <span className="text-lg shrink-0">{p.icon}</span>
            <span className="leading-relaxed flex-1">{p.text}</span>
            <span className="text-xs text-slate-400 group-hover:text-indigo-500 transition-colors shrink-0 mt-0.5">
              →
            </span>
          </button>
        ))}
      </div>
      <p className="text-[11px] text-slate-400 text-center mt-3 max-w-xl mx-auto">
        点击上方问题会填到输入框，可修改后再发送
      </p>
    </div>
  );
}

/* ---------- 消息气泡 ---------- */

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-2 sm:gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
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
            <div className="break-words">{renderMarkdown(msg.content)}</div>
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
          className={`flex items-center gap-2 mt-1 px-1 ${
            isUser ? "flex-row-reverse" : "flex-row"
          }`}
        >
          <span className="text-[10px] text-slate-400">
            {formatTime(msg.timestamp)}
          </span>
          {!isUser && msg.content && <CopyButton text={msg.content} />}
        </div>
      </div>
    </div>
  );
}
