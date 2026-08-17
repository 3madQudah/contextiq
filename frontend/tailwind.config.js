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
      // Marketing-only display sizes (Landing hero). Deliberately named apart
      // from the constrained in-app scale above so `text-2xl`/`text-3xl`
      // still resolve to nothing — the "two weights, six sizes" rule for
      // app UI stays enforced; only Landing reaches for these.
      "2xs": ["11.5px", { lineHeight: "16px" }],
      "display-xs": ["30px", { lineHeight: "36px", letterSpacing: "-0.01em" }],
      "display-sm": ["32px", { lineHeight: "38px", letterSpacing: "-0.01em" }],
      "display-md": ["44px", { lineHeight: "50px", letterSpacing: "-0.015em" }],
    },
    fontWeight: {
      normal: "400",
      medium: "500",
      // Marketing-only, same rationale as the display-* font sizes below —
      // in-app UI still only ever reaches for normal/medium.
      semibold: "600",
      bold: "700",
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
        success: "rgb(var(--color-success) / <alpha-value>)",
        // Decorative-only aurora hues — never used for text/foreground, only
        // for background glow/blob accents, so contrast rules never apply.
        "aurora-violet": "rgb(var(--color-aurora-violet) / <alpha-value>)",
        "aurora-cyan": "rgb(var(--color-aurora-cyan) / <alpha-value>)",
        "pipeline-surface": "rgb(var(--color-pipeline-surface) / <alpha-value>)",
        "pipeline-border": "rgb(var(--color-pipeline-border) / <alpha-value>)",
        "pipeline-label": "rgb(var(--color-pipeline-label) / <alpha-value>)",
      },
      borderRadius: {
        md: "6px",
        lg: "8px",
        xl: "12px",
        "2xl": "18px",
      },
      transitionDuration: {
        150: "150ms",
        200: "200ms",
      },
      boxShadow: {
        glass: "0 1px 1px rgb(0 0 0 / 0.03), 0 8px 24px -8px rgb(0 0 0 / 0.12)",
        "glass-lg": "0 2px 2px rgb(0 0 0 / 0.04), 0 16px 40px -12px rgb(0 0 0 / 0.18)",
        glow: "0 0 0 1px rgb(var(--color-accent) / 0.15), 0 8px 24px -8px rgb(var(--color-accent) / 0.35)",
      },
      backdropBlur: {
        xs: "2px",
      },
      keyframes: {
        "aurora-drift": {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(3%, -4%) scale(1.06)" },
          "66%": { transform: "translate(-3%, 3%) scale(0.96)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        // Pipeline diagram (Landing hero) — see PipelineDiagram.jsx.
        "pipeline-flow": {
          from: { strokeDashoffset: "108" },
          to: { strokeDashoffset: "0" },
        },
        "pipeline-hub-breathe": {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.05)" },
        },
        "pipeline-ripple": {
          "0%":   { transform: "scale(1)",    opacity: "0.45" },
          "100%": { transform: "scale(1.75)", opacity: "0" },
        },
        // One-time entrance (see PipelineDiagram.jsx): pure CSS, not Framer,
        // specifically so the diagram's visibility never depends on
        // whileInView/IntersectionObserver succeeding on SVG children (a
        // real WebKit/Safari gap). The `to` keyframe always matches the
        // element's plain, un-gated resting attribute value, so a failed
        // or unsupported animation still leaves the correct final state.
        "pipeline-line-in": {
          from: { strokeDashoffset: "100" },
          to: { strokeDashoffset: "0" },
        },
        "pipeline-pill-in": {
          from: { opacity: "0", transform: "translateX(-8px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        "pipeline-card-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "aurora-drift": "aurora-drift 18s ease-in-out infinite",
        "aurora-drift-slow": "aurora-drift 26s ease-in-out infinite reverse",
        shimmer: "shimmer 2s linear infinite",
        "pipeline-flow": "pipeline-flow 2.2s linear infinite",
        "pipeline-hub": "pipeline-hub-breathe 3.2s ease-in-out infinite",
        "pipeline-ripple": "pipeline-ripple 2.4s ease-out infinite",
        "pipeline-line-in": "pipeline-line-in 0.7s cubic-bezier(0.22,1,0.36,1) both",
        "pipeline-pill-in": "pipeline-pill-in 0.35s cubic-bezier(0.22,1,0.36,1) both",
        "pipeline-card-in": "pipeline-card-in 0.45s cubic-bezier(0.22,1,0.36,1) both",
      },
    },
  },
  plugins: [],
};
