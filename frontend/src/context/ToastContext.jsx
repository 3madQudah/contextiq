import { createContext, useCallback, useContext, useMemo, useState } from "react";

import ToastViewport from "../components/ToastViewport.jsx";

// App-wide toast queue. Purely additive UI feedback (upload finished,
// connection saved, item deleted, link copied) — it never replaces the
// inline errors/empty-states pages already render, those stay as the
// source of truth for anything the user must act on.
const ToastContext = createContext(null);
const DEFAULT_DURATION = 4000;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (message, { variant = "default", duration = DEFAULT_DURATION } = {}) => {
      const id = `${Date.now()}-${Math.random()}`;
      setToasts((prev) => [...prev, { id, message, variant, duration }]);
      return id;
    },
    []
  );

  const toast = useMemo(
    () => ({
      show: push,
      success: (message, opts) => push(message, { ...opts, variant: "success" }),
      error: (message, opts) => push(message, { ...opts, variant: "error" }),
    }),
    [push]
  );

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
