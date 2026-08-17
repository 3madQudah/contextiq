// Decorative gradient-blob backdrop shared by the marketing/auth pages —
// the "Aurora" half of this app's visual style (glass panels floating over
// a slow-drifting mesh of color). Pure CSS animation (see .aurora-orb /
// animate-aurora-drift* in index.css), disabled under prefers-reduced-motion.
// Purely decorative: aria-hidden, no interactive content, never affects layout.
export default function AuroraBackground({ className = "" }) {
  return (
    <div aria-hidden="true" className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}>
      <div
        className="aurora-orb animate-aurora-drift left-[-10%] top-[-15%] h-[420px] w-[420px] bg-accent/25 dark:bg-accent/30"
      />
      <div
        className="aurora-orb animate-aurora-drift-slow right-[-10%] top-[5%] h-[380px] w-[380px] bg-aurora-violet/20 dark:bg-aurora-violet/25"
      />
      <div
        className="aurora-orb animate-aurora-drift left-[20%] top-[40%] h-[320px] w-[320px] bg-aurora-cyan/10 dark:bg-aurora-cyan/15"
      />
    </div>
  );
}
