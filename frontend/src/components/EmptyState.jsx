export default function EmptyState({ icon: Icon, title, body, action }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-lg border border-border px-6 py-12 text-center">
      {Icon && <Icon size={22} strokeWidth={1.5} className="mb-1 text-muted" />}
      <h3 className="text-base font-medium text-foreground">{title}</h3>
      <p className="max-w-sm text-sm text-muted">{body}</p>
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
