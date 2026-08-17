import BrainMark from "./landing/BrainMark.jsx";

// App-shell brand mark (Sidebar + AppLayout's mobile header) — NOT used by
// the auth pages anymore (Login/Register use components/landing/AuthBrand.jsx
// instead), so this only affects the two in-app contexts.
export default function Logo({ size = "md", className = "" }) {
  const isSmall = size === "sm";
  const boxSize = isSmall ? 22 : 28;
  const iconSize = isSmall ? 14 : 18;
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className="flex shrink-0 items-center justify-center rounded-md bg-black"
        style={{ height: boxSize, width: boxSize }}
      >
        <BrainMark size={iconSize} inverted />
      </div>
      <span className={`font-medium text-foreground ${isSmall ? "text-base" : "text-md"}`}>
        ContextIQ
      </span>
    </div>
  );
}
