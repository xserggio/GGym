import type { Config } from "tailwindcss";

/**
 * Tokens extracted from the Claude Design prototype (/design). Colours are CSS
 * variables so the light/dark themes swap via the `data-tema` attribute on the
 * app root (see src/index.css). No screen component defines its own colours or
 * sizes — if a value is missing here, add it as a token.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        paper: "var(--paper)",
        ink: "var(--ink)",
        gris: "var(--gris)",
        line: "var(--line)",
        blue: "var(--blue)",
        green: "var(--green)",
        yellow: "var(--yellow)",
        red: "var(--red)",
        tint: "var(--tint)",
        thumbA: "var(--thumbA)",
        thumbB: "var(--thumbB)",
      },
      fontFamily: {
        display: ['"Instrument Serif"', "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        chip: "6px",
        field: "8px",
        card: "10px",
        sheet: "14px",
      },
      minHeight: {
        touch: "44px",
      },
      minWidth: {
        touch: "44px",
      },
      height: {
        touch: "44px",
      },
      width: {
        touch: "44px",
      },
    },
  },
  plugins: [],
} satisfies Config;
