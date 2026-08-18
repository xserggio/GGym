import type { CapacitorConfig } from "@capacitor/cli";

/**
 * Native shell around the same React app (no rewrite). The web assets ship
 * inside the package and are served from the device, so the API is reached at
 * its absolute URL and authentication uses the bearer token rather than the
 * cookie — see `crossOrigin` in src/lib/api.ts.
 *
 * Build with:  VITE_NATIVE=1 VITE_API_BASE=https://<host>/gym/api npm run build
 */
const config: CapacitorConfig = {
  appId: "com.ggym.app",
  appName: "GGym",
  webDir: "dist",
  android: {
    // The app talks to its own HTTPS backend; no plaintext traffic is allowed.
    allowMixedContent: false,
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 600,
      backgroundColor: "#E9E7E2",
    },
  },
};

export default config;
