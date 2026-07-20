import { useRef } from "react";
import { generateId, ts, SCENE_INFO, looksLikeSchoolRequest, extractInfo, getMissingFields, profileToInfo } from "../services/chat-helpers";
import { loadProfile, mergeChatInfo, createChatHistoryItem, addHistoryItem } from "../services/profile";
import { sendChat, streamChat, saveChatTurn } from "../services/chat";
import { logout as authLogout, isAuthenticated } from "../services/auth";
import { useAppStore } from "../store/appStore";
import type { ChatMessage } from "../types";
import type { SceneId } from "../config/scenes";

/** 生成唯一会话 ID */
function genSessionId(): string {
  return `chat_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

type SceneState = Record<SceneId, ChatMessage[]>;

/**
 * 聊天核心逻辑：发送消息 → 信息收集 → AI 调用 → 清空。
 *
 * 钩子外传入当前 render 的最新状态值，每次 render 产生新鲜函数引用。
 */
export function useChatSend(
  activeScene: SceneId,
  scenes: SceneState,
  setScenes: React.Dispatch<React.SetStateAction<SceneState>>,
  collectedInfo: Record<SceneId, Record<string, string>>,
  setCollectedInfo: (
    v:
      | Record<string, Record<string, string>>
      | ((prev: Record<string, Record<string, string>>) => Record<string, Record<string, string>>)
  ) => void,
  setLoading: React.Dispatch<React.SetStateAction<boolean>>,
  setError: React.Dispatch<React.SetStateAction<string | null>>,
  setInput: React.Dispatch<React.SetStateAction<string>>,
  inputRef: React.RefObject<HTMLTextAreaElement | null>,
  abortRef: React.MutableRefObject<AbortController | null>,
  loading: boolean,
  input: string,
  atBottomRef: React.MutableRefObject<boolean>,
) {
  const messages = scenes[activeScene] || [];
  const sendingRef = useRef(false);
  const sessionIdRef = useRef<Record<string, string>>({});

  const updateSceneMessages = (updater: (prev: ChatMessage[]) => ChatMessage[]) => {
    setScenes((prev: SceneState) => ({ ...prev, [activeScene]: updater(prev[activeScene]) }));
  };

  const handleStop = () => {
    abortRef.current?.abort();
  };

  const handleClear = () => {
    if (loading) handleStop();
    if (messages.length >= 2) {
      addHistoryItem(createChatHistoryItem(activeScene, messages));
    }
    setScenes((prev: SceneState) => ({ ...prev, [activeScene]: [] }));
    setCollectedInfo((prev: Record<SceneId, Record<string, string>>) => ({ ...prev, [activeScene]: {} }));
    setError(null);
    setInput("");
    sessionIdRef.current[activeScene] = genSessionId(); // 新会话 ID
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleClearAll = () => {
    if (loading) handleStop();
    if (!window.confirm("清空所有对话历史？此操作不可恢复。")) return;
    for (const [sid, msgs] of Object.entries(scenes)) {
      if (msgs.length >= 2) {
        addHistoryItem(createChatHistoryItem(sid as SceneId, msgs));
      }
    }
    setScenes({ school: [], essay: [], visa: [] });
    setCollectedInfo({} as Record<SceneId, Record<string, string>>);
    sessionIdRef.current = {}; // 重置所有会话 ID
  };

  const doSendToAI = async (msgs: ChatMessage[]) => {
    const assistantId = generateId();
    updateSceneMessages((prev: ChatMessage[]) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "", timestamp: ts() },
    ]);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const apiMessages = msgs.map((m: ChatMessage) => ({
        role: m.role as "user" | "assistant",
        content: m.content,
      }));

      let accumulated = "";
      let reasoningText = "";
      // rAF batching: cap React state updates at ~60fps during streaming
      // instead of firing setScenes on EVERY token (which freezes the page)
      let rAFContent = 0;
      let rAFReasoning = 0;

      const flushContent = () => {
        if (rAFContent) { cancelAnimationFrame(rAFContent); rAFContent = 0; }
        const current = accumulated;
        setScenes((prev: SceneState) => ({
          ...prev,
          [activeScene]: prev[activeScene].map((m: ChatMessage) =>
            m.id === assistantId ? { ...m, content: current } : m
          ),
        }));
      };

      const flushReasoning = () => {
        if (rAFReasoning) { cancelAnimationFrame(rAFReasoning); rAFReasoning = 0; }
        const current = reasoningText;
        setScenes((prev: SceneState) => ({
          ...prev,
          [activeScene]: prev[activeScene].map((m: ChatMessage) =>
            m.id === assistantId ? { ...m, reasoning: current } : m
          ),
        }));
      };

      await streamChat(
        apiMessages,
        (chunk: string) => {
          accumulated += chunk;
          if (!rAFContent) {
            rAFContent = requestAnimationFrame(() => {
              rAFContent = 0;
              const current = accumulated;
              setScenes((prev: SceneState) => ({
                ...prev,
                [activeScene]: prev[activeScene].map((m: ChatMessage) =>
                  m.id === assistantId ? { ...m, content: current } : m
                ),
              }));
            });
          }
        },
        () => {
          // flush any pending batched state on stream completion
          flushContent();
          flushReasoning();
          // 自动保存本轮到后端
          const lastUser = msgs.filter(m => m.role === "user").pop();
          if (lastUser && accumulated && !sessionIdRef.current[activeScene]) {
            sessionIdRef.current[activeScene] = genSessionId();
          }
          if (lastUser && accumulated) {
            saveChatTurn(
              sessionIdRef.current[activeScene],
              activeScene,
              lastUser.content,
              accumulated,
            );
          }
        },
        controller.signal,
        (reasoning: string) => {
          reasoningText += reasoning;
          if (!rAFReasoning) {
            rAFReasoning = requestAnimationFrame(() => {
              rAFReasoning = 0;
              const current = reasoningText;
              setScenes((prev: SceneState) => ({
                ...prev,
                [activeScene]: prev[activeScene].map((m: ChatMessage) =>
                  m.id === assistantId ? { ...m, reasoning: current } : m
                ),
              }));
            });
          }
        }
      );
    } catch (e: any) {
      if (e?.name === "AbortError") {
        setScenes((prev: SceneState) => ({
          ...prev,
          [activeScene]: prev[activeScene].map((m: ChatMessage) =>
            m.id === assistantId && !m.content
              ? { ...m, content: "_（已停止生成）_" }
              : m
          ),
        }));
      } else {
        try {
          const apiMessages = msgs.map((m: ChatMessage) => ({
            role: m.role as "user" | "assistant",
            content: m.content,
          }));
          const res = await sendChat(apiMessages);
          setScenes((prev: SceneState) => ({
            ...prev,
            [activeScene]: prev[activeScene].map((m: ChatMessage) =>
              m.id === assistantId ? { ...m, content: res.reply } : m
            ),
          }));
          // 自动保存本轮到后端
          const lastUser = msgs.filter(m => m.role === "user").pop();
          if (lastUser && res.reply) {
            if (!sessionIdRef.current[activeScene]) {
              sessionIdRef.current[activeScene] = genSessionId();
            }
            saveChatTurn(
              sessionIdRef.current[activeScene],
              activeScene,
              lastUser.content,
              res.reply,
            );
          }
        } catch (retryErr: unknown) {
          const msg = retryErr instanceof Error ? retryErr.message : "";
          let errorMsg = "网络连接失败，请检查网络后重试";
          let contentMsg = "抱歉，请求失败，请稍后重试。";
          if (msg.includes("试用")) {
            errorMsg = "试用次数已用完，请登录后继续使用";
            contentMsg = "试用次数已用完，请登录后继续使用。";
            setTimeout(() => {
              window.location.hash = `#/login?redirect=${encodeURIComponent(window.location.hash.slice(1) || "/chat")}`;
            }, 2000);
          } else if (msg.includes("授权码") || msg.includes("X-Auth-Code") || msg.includes("401")) {
            errorMsg = "授权已过期，请重新登录";
            contentMsg = "授权已过期，请重新登录后再试。";
            authLogout();
            setTimeout(() => { window.location.hash = "#/login"; }, 2000);
          } else if (msg.includes("余额")) {
            errorMsg = "AI 服务暂不可用（余额不足），请联系管理员";
            contentMsg = "AI 服务暂不可用，请联系管理员处理。";
          } else if (msg.includes("对话服务异常")) {
            errorMsg = "AI 服务暂时不可用（OpenCode API 异常），请稍后重试";
            contentMsg = "AI 服务暂时不可用，请稍后重试。";
          } else if (msg.includes("500")) {
            errorMsg = "服务端处理出错，已记录日志，请稍后重试";
          } else if (msg.includes("timeout") || msg.includes("超时")) {
            errorMsg = "请求超时，请稍后重试";
          } else if (msg.includes("429") || msg.includes("Too Many Requests")) {
            errorMsg = "请求过于频繁，请稍后再试";
          }
          setError(errorMsg);
          setScenes((prev: SceneState) => ({
            ...prev,
            [activeScene]: prev[activeScene].map((m: ChatMessage) =>
              m.id === assistantId && !m.content
                ? { ...m, content: contentMsg }
                : m
            ),
          }));
        }
      }
    } finally {
      setLoading(false);
      sendingRef.current = false;
      if (abortRef.current === controller) {
        abortRef.current = null;
      }
      inputRef.current?.focus();
    }
  };

  const handleSend = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || loading || sendingRef.current) return;
    // 试用拦截：已用完试用且未登录 → 直接跳登录页，不发送请求
    if (useAppStore.getState().trialUsed && !isAuthenticated()) {
      window.location.hash = `#/login?redirect=${encodeURIComponent(window.location.hash.slice(1) || "/chat")}`;
      return;
    }
    sendingRef.current = true;
    setError(null);

    try {
      const userMsg: ChatMessage = {
        id: generateId(),
        role: "user",
        content,
        timestamp: ts(),
      };

      const updatedMessages = [...messages, userMsg];
      updateSceneMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);
      atBottomRef.current = true;

      const isSchoolRequest = activeScene === "school" && looksLikeSchoolRequest(content);
      if (isSchoolRequest) {
        const currentInfo = collectedInfo[activeScene] || {};
        const fields = SCENE_INFO[activeScene];

        let baseInfo: Record<string, string> = {};
        if (!collectedInfo[activeScene] || Object.keys(currentInfo).length === 0) {
          const profile = loadProfile();
          if (profile) baseInfo = profileToInfo(profile);
        }

        const newInfo = { ...baseInfo, ...currentInfo, ...(await extractInfo(content)) };
        const missing = getMissingFields(newInfo, fields);

        if (!collectedInfo[activeScene] && missing.length > 0) {
          const nextField = missing[0];
          setCollectedInfo((prev: Record<SceneId, Record<string, string>>) => ({ ...prev, [activeScene]: newInfo }));
          updateSceneMessages((prev: ChatMessage[]) => [
            ...prev,
            {
              id: generateId(),
              role: "assistant",
              content: `收到您提供的信息，但还有一些不清楚的地方，需要跟您进一步确认：\n\n**${nextField.prompt}**\n\n提示：${nextField.hint}`,
              timestamp: ts(),
            },
          ]);
          setLoading(false);
          sendingRef.current = false;
          return;
        }

        if (missing.length === 0 && !collectedInfo[activeScene]) {
          setCollectedInfo((prev: Record<SceneId, Record<string, string>>) => ({ ...prev, [activeScene]: newInfo }));
          mergeChatInfo(newInfo);
          // 不修改用户消息，原文直发
          await doSendToAI(updatedMessages);
          return;
        }

        if (collectedInfo[activeScene] && Object.keys(collectedInfo[activeScene]).length > 0) {
          const hasNewInfo = Object.keys(newInfo).length > Object.keys(currentInfo).length;
          if (hasNewInfo) {
            setCollectedInfo((prev: Record<SceneId, Record<string, string>>) => ({ ...prev, [activeScene]: newInfo }));
            mergeChatInfo(newInfo);
          }
          // 不修改用户消息，原文直发
          await doSendToAI(updatedMessages);
          return;
        }

        await doSendToAI(updatedMessages);
        return;
      }

      if (activeScene === "school" && collectedInfo[activeScene]) {
        // AI 已经回复过 → 进入正常多轮问答，不再重新提取信息
        const aiReplied = messages.some(m => m.role === "assistant");
        if (aiReplied) {
          // 继续补充新提取的信息（如有）
          const currentInfo = collectedInfo[activeScene] || {};
          const newInfo = { ...currentInfo, ...(await extractInfo(content)) };
          const hasNewInfo = Object.keys(newInfo).length > Object.keys(currentInfo).length;
          if (hasNewInfo) {
            setCollectedInfo((prev: Record<SceneId, Record<string, string>>) => ({ ...prev, [activeScene]: newInfo }));
            mergeChatInfo(newInfo);
          }
          await doSendToAI(updatedMessages);
          return;
        }

        const currentInfo = collectedInfo[activeScene] || {};
        const fields = SCENE_INFO[activeScene];
        const newInfo = { ...currentInfo, ...(await extractInfo(content)) };
        const missing = getMissingFields(newInfo, fields);

        if (missing.length > 0) {
          const nextField = missing[0];
          setCollectedInfo((prev: Record<SceneId, Record<string, string>>) => ({ ...prev, [activeScene]: newInfo }));
          updateSceneMessages((prev: ChatMessage[]) => [
            ...prev,
            {
              id: generateId(),
              role: "assistant",
              content: `好的，还差最后几项：\n\n**${nextField.prompt}**\n\n提示：${nextField.hint}`,
              timestamp: ts(),
            },
          ]);
          setLoading(false);
          sendingRef.current = false;
          return;
        }

        setCollectedInfo((prev: Record<SceneId, Record<string, string>>) => ({ ...prev, [activeScene]: newInfo }));
        mergeChatInfo(newInfo);
        // 不修改用户消息，原文直发
        await doSendToAI(updatedMessages);
        return;
      }

      await doSendToAI(updatedMessages);
    } catch (err) {
      console.error("handleSend failed:", err);
      const msg = err instanceof Error ? err.message : "";
      // "Failed to fetch" is a browser TypeError — network unreachable, not auth/data issue
      if (msg.includes("Failed to fetch") || msg.includes("NetworkError") || msg.includes("fetch")) {
        setError("网络连接异常，请检查网络后重试");
      } else if (msg) {
        setError(msg);
      } else {
        setError("请求处理失败");
      }
      setLoading(false);
      sendingRef.current = false;
    }
  };

  return { handleSend, handleStop, handleClear, handleClearAll };
}
