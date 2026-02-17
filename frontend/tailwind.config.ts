import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        okx: {
          bg: "#0b0e11",
          card: "#12161c",
          border: "#1e2329",
          hover: "#1b2028",
          text: "#eaecef",
          muted: "#848e9c",
          dim: "#474d57",
          green: "#0ecb81",
          red: "#f6465d",
          gold: "#fcd535",
          blue: "#1e9fff",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Microsoft YaHei", "sans-serif"],
        mono: ["JetBrains Mono", "SF Mono", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;



