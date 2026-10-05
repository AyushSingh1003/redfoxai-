import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        // Disable response buffering so SSE (text/event-stream) is streamed live
        configure: (_proxy, _options) => {
          _proxy.on("proxyRes", (proxyRes) => {
            if (
              proxyRes.headers["content-type"]?.startsWith("text/event-stream")
            ) {
              // @ts-expect-error - flush headers immediately for SSE
              proxyRes.flushHeaders?.();
            }
          });
        },
      },
      "/health": "http://127.0.0.1:8000",
      "/docs": "http://127.0.0.1:8000",
      "/openapi.json": "http://127.0.0.1:8000",
    },
  },
});
