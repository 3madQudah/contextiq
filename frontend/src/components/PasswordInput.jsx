import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";

export default function PasswordInput({ label, error, hint, className = "", id, ...props }) {
  const [visible, setVisible] = useState(false);
  const inputId = id || props.name;

  return (
    <div className={className}>
      {label && (
        <label htmlFor={inputId} className="mb-1.5 block text-sm text-muted">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          id={inputId}
          type={visible ? "text" : "password"}
          className={`w-full rounded-md border bg-surface px-3 py-2 pr-9 text-base text-foreground placeholder:text-muted focus-visible:ring-2 focus-visible:ring-accent/40 ${
            error ? "border-danger" : "border-border"
          }`}
          {...props}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          tabIndex={-1}
          className="absolute inset-y-0 right-0 flex w-9 items-center justify-center text-muted hover:text-foreground"
        >
          {visible ? <EyeOff size={16} strokeWidth={1.5} /> : <Eye size={16} strokeWidth={1.5} />}
        </button>
      </div>
      {error ? (
        <p className="mt-1.5 text-sm text-danger">{error}</p>
      ) : hint ? (
        <p className="mt-1.5 text-sm text-muted">{hint}</p>
      ) : null}
    </div>
  );
}
