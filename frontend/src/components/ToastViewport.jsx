import { AnimatePresence, motion } from "motion/react";
import { CheckCircle2, X, XCircle } from "lucide-react";
import { useEffect } from "react";

const ICONS = {
  success: CheckCircle2,
  error: XCircle,
  default: CheckCircle2,
};

const ICON_COLOR = {
  success: "text-success",
  error: "text-danger",
  default: "text-accent",
};

function ToastItem({ toast, onDismiss }) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(toast.id), toast.duration);
    return () => clearTimeout(timer);
  }, [toast, onDismiss]);

  const Icon = ICONS[toast.variant] || ICONS.default;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: 32, transition: { duration: 0.15 } }}
      transition={{ type: "spring", stiffness: 400, damping: 32 }}
      className="glass-panel pointer-events-auto flex w-full max-w-sm items-start gap-2.5 rounded-lg border border-border px-3.5 py-3 shadow-glass-lg"
      role="status"
      aria-live="polite"
    >
      <Icon size={16} strokeWidth={1.5} className={`mt-0.5 shrink-0 ${ICON_COLOR[toast.variant]}`} />
      <p className="flex-1 text-sm text-foreground">{toast.message}</p>
      <button
        type="button"
        aria-label="Dismiss notification"
        onClick={() => onDismiss(toast.id)}
        className="shrink-0 text-muted hover:text-foreground"
      >
        <X size={14} strokeWidth={1.5} />
      </button>
    </motion.div>
  );
}

export default function ToastViewport({ toasts, onDismiss }) {
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-0 z-[100] flex flex-col items-end gap-2 p-4 sm:bottom-4 sm:right-4 sm:left-auto">
      <AnimatePresence>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
        ))}
      </AnimatePresence>
    </div>
  );
}
