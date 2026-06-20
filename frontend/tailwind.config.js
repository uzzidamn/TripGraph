/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#080c18",
        surface: "rgba(14, 18, 38, 0.85)",
        "surface-hover": "rgba(22, 28, 58, 0.92)",
        border: "rgba(255, 255, 255, 0.07)",
        "border-light": "rgba(255, 255, 255, 0.13)",
        "text-primary": "#e2e8f0",
        "text-muted": "#64748b",
        primary: "#7c6df7",
        "primary-hover": "#9080ff",
        accent: "#00cec9",
        success: "#00b894",
        warning: "#fdcb6e",
        danger: "#e17055",
        "panel-bg": "rgba(8, 12, 26, 0.9)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
