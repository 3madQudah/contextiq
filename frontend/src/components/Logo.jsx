export default function Logo({ size = "md", className = "" }) {
  const isSmall = size === "sm";
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className={`flex items-center justify-center rounded-md bg-accent text-accent-foreground font-medium ${
          isSmall ? "h-6 w-6 text-sm" : "h-8 w-8 text-md"
        }`}
      >
        C
      </div>
      <span className={`font-medium text-foreground ${isSmall ? "text-base" : "text-md"}`}>
        ContextIQ
      </span>
    </div>
  );
}
