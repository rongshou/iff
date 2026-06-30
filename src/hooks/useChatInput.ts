import { useCallback, useRef, useState } from "react";

/**
 * 聊天输入框的状态与键盘行为。
 *
 * 抽离自 ChatPage：管理 input 文本、inputRef 聚焦引用，
 * 以及 Enter 发送（Shift+Enter 换行）的 keydown 处理。
 *
 * 通过 ref 持有最新的 onSend，使 handleKeyDown 保持稳定引用，
 * 同时避免在 handleSend 定义之前调用 hook 造成的 TDZ。
 *
 * @param onSend 按下 Enter（不带 Shift）时触发的发送回调。
 */
export function useChatInput(onSend: () => void) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const sendRef = useRef(onSend);
  sendRef.current = onSend;

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendRef.current();
      }
    },
    []
  );

  return { input, setInput, inputRef, handleKeyDown };
}