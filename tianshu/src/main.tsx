/**
 * tianshu React 入口（步骤 2 - 共用 BrandNav）
 *
 * 现状：
 * - tianquan 已用 BrandNav（commit 57ed170）
 * - tianshu 这里是 Vite + React 入口，但**只渲染 BrandNav**
 * - 旧测评功能（5 步表单）由 src/web/ 下的原生 JS 提供，不动
 *
 * 步骤 3 会逐步把各 step 迁移到 React。
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);