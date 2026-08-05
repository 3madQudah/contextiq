import { ArrowUp, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export default function Composer({
  onSend,
  disabled,
  activeFilter,
  onClearFilter,
  placeholder = "Ask a question about your documents…",
}) {
  const [value, setValue] = useState("");
  const textareaRef = useRef(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  function handleSend() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="border-t border-border bg-bg px-4 py-3">
      <div className="mx-auto max-w-2xl">
        {activeFilter && (
          <div className="mb-2 flex">
            <button
              type="button"
              onClick={onClearFilter}
              className="inline-flex items-center gap-1.5 rounded-full border border-accent/30 bg-accent/10 px-2.5 py-1 text-xs text-accent"
            >
              Filtering: .{activeFilter}
              <X size={12} strokeWidth={1.5} />
            </button>
          </div>
        )}

        <div className="flex items-end gap-2 rounded-lg border border-border bg-surface px-3 py-2">
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="max-h-40 flex-1 resize-none bg-transparent text-base text-foreground placeholder:text-muted focus:outline-none"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={disabled || !value.trim()}
            aria-label="Send message"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent text-accent-foreground transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ArrowUp size={16} strokeWidth={1.5} />
          </button>
        </div>
      </div>
    </div>
  );
}
