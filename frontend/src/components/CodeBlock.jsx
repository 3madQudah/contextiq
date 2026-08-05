import { Check, Copy } from "lucide-react";
import { useState } from "react";

export default function CodeBlock({ code }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard permission denied/unavailable — button just won't confirm.
    }
  }

  return (
    <div className="relative rounded-lg bg-surface-hover">
      <button
        type="button"
        onClick={handleCopy}
        aria-label="Copy SQL"
        className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-md text-muted hover:bg-surface hover:text-foreground"
      >
        {copied ? <Check size={14} strokeWidth={1.5} /> : <Copy size={14} strokeWidth={1.5} />}
      </button>
      <pre className="overflow-x-auto p-3 pr-10 text-sm">
        <code className="font-mono text-foreground">{code}</code>
      </pre>
    </div>
  );
}
