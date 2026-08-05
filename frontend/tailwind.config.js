/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    // Replacing (not extending) fontSize/fontWeight is deliberate: it's the
    // enforcement mechanism for the "two weights, six sizes" rule — a stray
    // font-bold or text-3xl simply won't generate any CSS.
    fontSize: {
      xs: ["12px", { lineHeight: "16px" }],
      sm: ["13px", { lineHeight: "18px" }],
      base: ["14px", { lineHeight: "20px" }],
      md: ["16px", { lineHeight: "24px" }],
      lg: ["20px", { lineHeight: "28px" }],
      xl: ["24px", { lineHeight: "32px" }],
    },
    fontWeight: {
      normal: "400",
      medium: "500",
    },
    extend: {
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Inter",
          "Segoe UI",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      colors: {
        bg: "rgb(var(--color-bg) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        "surface-hover": "rgb(var(--color-surface-hover) / <alpha-value>)",
        border: "rgb(var(--color-border) / <alpha-value>)",
        foreground: "rgb(var(--color-foreground) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        "accent-foreground": "rgb(var(--color-accent-foreground) / <alpha-value>)",
        danger: "rgb(var(--color-danger) / <alpha-value>)",
        "danger-foreground": "rgb(var(--color-danger-foreground) / <alpha-value>)",
      },
      borderRadius: {
        md: "6px",
        lg: "8px",
      },
      transitionDuration: {
        150: "150ms",
        200: "200ms",
      },
    },
  },
  plugins: [],
};
