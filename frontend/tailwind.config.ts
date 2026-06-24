import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Paleta exacta de PLAN §2.
        bg: "#0d1117",
        panel: "#1a1a2e",
        "panel-2": "#161625",
        border: "#272735",
        muted: "#8b8ba0",
        accent: "#ecad0a",
        primary: "#209dd7",
        secondary: "#753991",
        up: "#16c784",
        down: "#ea3943",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      keyframes: {
        pulse_dot: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.4", transform: "scale(0.8)" },
        },
      },
      animation: {
        "pulse-dot": "pulse_dot 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
