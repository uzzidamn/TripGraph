/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0f1117",
        surface: "#1a1d2e",
        "surface-hover": "#242842",
        border: "#2a2e45",
        "text-primary": "#e4e6f0",
        "text-muted": "#8b8fa3",
        primary: "#6c5ce7",
        "primary-hover": "#7d6ff0",
        accent: "#00cec9",
        success: "#00b894",
        warning: "#fdcb6e",
        danger: "#e17055",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
