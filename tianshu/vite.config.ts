import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// tianshu Vite 配置（步骤 2 - 共用 BrandNav 顶栏）
// - 单独构建到 ./dist/（不与 tianquan 冲突）
// - base 通过 CLI --base 覆盖（CI 用 /iff/tianshu/，自托管用 /tianshu/）
export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/tianshu/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});