import { Loader2 } from "lucide-react";

const VARIANTS = {
  primary: "bg-accent text-accent-foreground hover:opacity-90",
  secondary: "bg-surface border border-border text-foreground hover:bg-surface-hover",
  ghost: "text-foreground hover:bg-surface-hover",
  danger: "bg-danger text-danger-foreground hover:opacity-90",
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
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-md px-3.5 py-2 text-base font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
      {...props}
    >
      {loading && <Loader2 size={15} strokeWidth={1.5} className="animate-spin" />}
      {children}
    </button>
  );
}
