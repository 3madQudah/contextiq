export default function TextInput({ label, error, hint, className = "", id, ...props }) {
  const inputId = id || props.name;
  return (
    <div className={className}>
      {label && (
        <label htmlFor={inputId} className="mb-1.5 block text-sm text-muted">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`w-full rounded-md border bg-surface px-3 py-2 text-base text-foreground placeholder:text-muted focus-visible:ring-2 focus-visible:ring-accent/40 ${
          error ? "border-danger" : "border-border"
        }`}
        {...props}
      />
      {error ? (
        <p className="mt-1.5 text-sm text-danger">{error}</p>
      ) : hint ? (
        <p className="mt-1.5 text-sm text-muted">{hint}</p>
      ) : null}
    </div>
  );
}
