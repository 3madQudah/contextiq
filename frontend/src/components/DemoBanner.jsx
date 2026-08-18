import { Info, X } from "lucide-react";
import { useState } from "react";

// Understated, dismissible notice shown across the authed app (see AppLayout)
// — not just the landing page — because this is deployed on free-tier infra
// where uploaded documents/indexes are wiped on redeploy and the free-tier
// database expires periodically (see docs/14-DEPLOYMENT.md). Dismissal is
// remembered in localStorage, matching the app's other one-shot flags
// (e.g. contextiq.hasUploadedBefore, contextiq.theme). Uses only existing
// design tokens (surface-hover / border / muted / foreground) — no new tokens.
const DISMISS_KEY = "contextiq.demoBannerDismissed";

export default function DemoBanner() {
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem(DISMISS_KEY) === "1"
  );

  if (dismissed) return null;

  function dismiss() {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  }

  return (
    <div className="flex items-start gap-2 border-b border-border bg-surface-hover px-4 py-2 text-sm text-muted">
      <Info size={15} strokeWidth={1.5} className="mt-0.5 shrink-0" />
      <p className="flex-1">
        Demo deployment — uploaded documents and their indexes are cleared on each
        redeploy. Accounts and conversations are stored in a free-tier database that
        expires periodically.
      </p>
      <button
        type="button"
        aria-label="Dismiss notice"
        onClick={dismiss}
        className="shrink-0 text-muted transition-colors hover:text-foreground"
      >
        <X size={14} strokeWidth={1.5} />
      </button>
    </div>
  );
}
