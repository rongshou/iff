import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: process.env.BASE_URL || "/",
  server: {
    proxy: {
      "/api": "http://localhost:3470",
    },
  },
  build: {
    outDir: "dist",
  },
});
