import { AnimatePresence, motion } from "framer-motion";
import { useEffect } from "react";

import Button from "./Button.jsx";

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Delete",
  danger = true,
  onConfirm,
  onCancel,
  loading = false,
}) {
  useEffect(() => {
    if (!open) return;
    function onKey(e) {
      if (e.key === "Escape") onCancel();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={onCancel}
        >
          <motion.div
            initial={{ opacity: 0, y: 4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            role="dialog"
            aria-modal="true"
            className="w-full max-w-sm rounded-lg border border-border bg-surface p-5 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-base font-medium text-foreground">{title}</h2>
            {description && <p className="mt-2 text-sm text-muted">{description}</p>}
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="secondary" onClick={onCancel}>
                Cancel
              </Button>
              <Button variant={danger ? "danger" : "primary"} onClick={onConfirm} loading={loading}>
                {confirmLabel}
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
