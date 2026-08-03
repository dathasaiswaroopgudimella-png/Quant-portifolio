import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        stitch: {
          surface: "#131315",
          "surface-dim": "#131315",
          "surface-bright": "#39393b",
          "surface-lowest": "#0e0e10",
          "surface-low": "#1c1b1d",
          "surface-container": "#201f22",
          "surface-high": "#2a2a2c",
          "surface-highest": "#353437",
          "on-surface": "#e5e1e4",
          "on-surface-variant": "#c7c4d7",
          outline: "#908fa0",
          "outline-variant": "#464554",
          primary: "#c0c1ff",
          "on-primary": "#1000a9",
          "primary-container": "#8083ff",
          secondary: "#4edea3",
          "on-secondary": "#003824",
          "secondary-container": "#00a572",
          tertiary: "#ffb95f",
          "on-tertiary": "#472a00",
          "tertiary-container": "#ca8100",
          error: "#ffb4ab",
          "error-container": "#93000a",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
