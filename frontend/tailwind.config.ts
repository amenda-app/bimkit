import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        dcab: {
          navy: "#1B3A5C",
          blue: "#2E6DA4",
          light: "#E8EDF2",
          accent: "#D4A843",
          dark: "#0F2235",
          gray: "#6B7B8D",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
