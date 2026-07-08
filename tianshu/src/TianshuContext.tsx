/**
 * TianshuContext - 天枢测评全局状态管理
 *
 * sub-3.1 实现：
 * - React Context + useState 替代旧 app.js 的全局 state 对象
 * - 提供 setState / goNext / goPrev / goTo
 * - 后续 sub-step 会扩展：localStorage 持久化、表单更新函数等
 */

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { DEFAULT_STATE, type TianshuContextValue, type TianshuState } from "./types";

const TianshuContext = createContext<TianshuContextValue | null>(null);

export function TianshuProvider({ children }: { children: ReactNode }) {
  const [state, setStateRaw] = useState<TianshuState>(DEFAULT_STATE);

  const setState = useCallback(
    (updater: Partial<TianshuState> | ((s: TianshuState) => Partial<TianshuState>)) => {
      setStateRaw((prev) => {
        const patch = typeof updater === "function" ? updater(prev) : updater;
        return { ...prev, ...patch };
      });
    },
    []
  );

  const goNext = useCallback(() => {
    setStateRaw((prev) => ({
      ...prev,
      step: Math.min(5, prev.step + 1) as 1 | 2 | 3 | 4 | 5,
    }));
  }, []);

  const goPrev = useCallback(() => {
    setStateRaw((prev) => ({
      ...prev,
      step: Math.max(1, prev.step - 1) as 1 | 2 | 3 | 4 | 5,
    }));
  }, []);

  const goTo = useCallback((step: 1 | 2 | 3 | 4 | 5) => {
    setStateRaw((prev) => ({ ...prev, step }));
  }, []);

  return (
    <TianshuContext.Provider value={{ state, setState, goNext, goPrev, goTo }}>
      {children}
    </TianshuContext.Provider>
  );
}

export function useTianshu(): TianshuContextValue {
  const ctx = useContext(TianshuContext);
  if (!ctx) throw new Error("useTianshu must be used within <TianshuProvider>");
  return ctx;
}