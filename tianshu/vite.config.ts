import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// tianshu Vite 配置（步骤 2 - 共用 BrandNav 顶栏）
// - 单独构建到 ./dist/（不与 tianquan 冲突）
// - base 设为 /tianshu/（与 nginx 路径对齐）
export default defineConfig({
  plugins: [react()],
  base: "/tianshu/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});