import { useCallback, useRef, useState } from "react";

export function useChatScroll() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
    if (atBottom) setShowScrollBottom(false);
    else setShowScrollBottom(true);
  }, []);

  const scrollToBottom = () => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
      setShowScrollBottom(false);
    }
  };

  return { scrollRef, showScrollBottom, setShowScrollBottom, onScroll, scrollToBottom };
}
