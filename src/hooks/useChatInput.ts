import { useCallback, useRef, useState } from "react";

/**
 * 聊天输入框的状态与键盘行为。
 * 使用 ref 存储发送回调，避免钩子调用必须在 handleSend 定义之后。
 */
export function useChatInput() {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const sendRef = useRef<() => void>(() => {});

  const setSendHandler = useCallback((fn: () => void) => {
    sendRef.current = fn;
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendRef.current();
      }
    },
    []
  );

  return { input, setInput, inputRef, handleKeyDown, setSendHandler };
}
