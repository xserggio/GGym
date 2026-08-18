/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { defineConfig } from "vitest/config";

// Served under /gym/ in production (behind the VPS nginx); root in dev.
// The native build (VITE_NATIVE=1) is served from the device itself, so it must
// use a root base and ship no service worker: assets are already local, and a
// worker caching localhost would only get in the way.
export default defineConfig(({ mode }) => {
  const native = process.env.VITE_NATIVE === "1";
  const base = mode === "production" && !native ? "/gym/" : "/";
  return {
  base,
  plugins: [
    react(),
    VitePWA({
      disable: native,
      registerType: "autoUpdate",
      injectRegister: "auto",
      scope: base,
      // Precache the app shell only; the API stays network-only so cookies work
      // and data is never served stale (offline durability is the Dexie queue).
      workbox: {
        globPatterns: ["**/*.{js,css,html,png,svg,woff2}"],
        navigateFallbackDenylist: [/\/api\//],
        // Daily reminder (spec §7.6): push/notificationclick handlers.
        importScripts: ["push-sw.js"],
        // Exercise photos are immutable; cache each one after it's first viewed
        // so they show offline without bloating the install-time precache.
        runtimeCaching: [
          {
            urlPattern: ({ url }) =>
              url.pathname.includes("/exercises/") && url.pathname.endsWith(".webp"),
            handler: "CacheFirst",
            options: {
              cacheName: "exercise-images",
              expiration: { maxEntries: 120, maxAgeSeconds: 60 * 60 * 24 * 90 },
            },
          },
        ],
      },
      manifest: {
        scope: base,
        start_url: base,
        name: "GGym",
        short_name: "GGym",
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
