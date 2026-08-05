import { FileText } from "lucide-react";

export default function SourceChip({ source, onClick }) {
  return (
    <button
      type="button"
      onClick={() => onClick(source)}
      title={`Filter the next question to ${source}`}
      className="inline-flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-xs text-muted transition-colors hover:border-accent/40 hover:text-accent"
    >
      <FileText size={11} strokeWidth={1.5} />
      {source}
    </button>
  );
}
