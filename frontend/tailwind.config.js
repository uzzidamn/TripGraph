/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Apple light-aluminum palette — cool, restrained, no dark colors.
        // Names match the v1 dark theme so existing class-level usages still work;
        // values are inverted so they read as a light-mode design system.
        ink:       "#f5f5f7",   // app background (was dark; now Apple's typical light grey)
        graphite:  "#ececef",   // lifted surface
        steel:     "#e3e4ea",   // primary surface
        aluminum:  "#cccdd4",   // raised / darker surface
        silver:    "#6e7382",   // secondary text / dim
        chrome:    "#2a2d33",   // primary text
        platinum:  "#0a0c10",   // highest-contrast text
        rim:       "rgba(0,0,0,0.10)",
        rimBright: "rgba(0,0,0,0.18)",
        hush:      "rgba(0,0,0,0.04)",
        whisper:   "rgba(255,255,255,0.65)",
      },
      fontFamily: {
        sans:    ["Inter", "system-ui", "-apple-system", "sans-serif"],
        display: ["Inter", "system-ui", "sans-serif"],
      },
      backdropBlur: {
        xs: "4px",
        md: "16px",
        lg: "28px",
        xl: "40px",
      },
      boxShadow: {
        glass: "0 1px 0 rgba(255,255,255,0.8) inset, 0 16px 48px rgba(20,22,28,0.10)",
        rim:   "0 0 0 1px rgba(0,0,0,0.06) inset",
      },
    },
  },
  plugins: [],
};
