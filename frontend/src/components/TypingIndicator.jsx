export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-1" aria-label="Assistant is typing">
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted [animation-delay:0ms]" />
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted [animation-delay:150ms]" />
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted [animation-delay:300ms]" />
    </div>
  );
}
