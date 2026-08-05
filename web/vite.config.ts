/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { defineConfig } from "vitest/config";

// Served under /gym/ in production (behind the VPS nginx); root in dev.
export default defineConfig(({ mode }) => {
  const base = mode === "production" ? "/gym/" : "/";
  return {
  base,
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      injectRegister: "auto",
      scope: base,
      // Precache the app shell only; the API stays network-only so cookies work
      // and data is never served stale (offline durability is the Dexie queue).
      workbox: {
        globPatterns: ["**/*.{js,css,html,png,svg,woff2}"],
        navigateFallbackDenylist: [/\/api\//],
      },
      manifest: {
        scope: base,
        start_url: base,
        name: "Registro de fuerza",
        short_name: "Fuerza",
        lang: "es",
        description: "Registro de entrenamientos de fuerza",
        theme_color: "#E9E7E2",
        background_color: "#E9E7E2",
        display: "standalone",
        // Relative to the manifest URL, so they resolve under the base path.
        icons: [
          { src: "icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icon-512.png", sizes: "512x512", type: "image/png" },
          {
            src: "icon-maskable-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    // Dev proxy to the FastAPI backend so cookies are same-origin in dev.
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
  };
});
