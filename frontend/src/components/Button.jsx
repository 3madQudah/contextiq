import { Loader2 } from "lucide-react";
import { motion } from "motion/react";

const VARIANTS = {
  primary: "bg-accent text-accent-foreground hover:opacity-90",
  secondary: "bg-surface border border-border text-foreground hover:bg-surface-hover",
  ghost: "text-foreground hover:bg-surface-hover",
  danger: "bg-danger text-danger-foreground hover:opacity-90",
  // Fixed (non-theme-adaptive) white/black treatment — a specific corrective
  // spec for the public-site "Get started" CTA, not a themed token, so it
  // intentionally doesn't invert with dark mode.
  invert: "bg-white text-black border border-zinc-300 hover:bg-zinc-50",
};

export default function Button({
  variant = "primary",
  loading = false,
  disabled = false,
  className = "",
  children,
  type = "button",
  ...props
}) {
  const isDisabled = disabled || loading;
  return (
    <motion.button
      type={type}
      disabled={isDisabled}
      whileHover={isDisabled ? undefined : { scale: 1.015 }}
      whileTap={isDisabled ? undefined : { scale: 0.96 }}
      transition={{ type: "spring", stiffness: 420, damping: 30 }}
      className={`inline-flex items-center justify-center gap-2 rounded-md px-3.5 py-2 text-base font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
      {...props}
    >
      {loading && <Loader2 size={15} strokeWidth={1.5} className="animate-spin" />}
      {children}
    </motion.button>
  );
}
