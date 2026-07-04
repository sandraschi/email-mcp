import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      external: ["@tauri-apps/api/window"],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    allowedHosts: ["goliath"],
    port: 10812,
    strictPort: true,
    host: "127.0.0.1",
    proxy: {
      "/api": "http://127.0.0.1:10813",
      "/mcp": "http://127.0.0.1:10813",
      "/docs": "http://127.0.0.1:10813",
      "/redoc": "http://127.0.0.1:10813",
      "/openapi.json": "http://127.0.0.1:10813",
    },
  },
});
