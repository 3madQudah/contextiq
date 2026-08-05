import { Loader2 } from "lucide-react";

export default function FullPageSpinner() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-bg">
      <Loader2 size={20} strokeWidth={1.5} className="animate-spin text-muted" />
    </div>
  );
}
