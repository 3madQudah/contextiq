// Brand mark for the public site (nav bar + hero diagram hub) — NOT the
// shared in-app Logo (that stays untouched so Sidebar/Login/Register/
// AppLayout are unaffected).
//
// Path data below is copied verbatim from the approved reference markup —
// do not regenerate/reinterpret these paths. Colors are literal (#000000 /
// #FFFFFF), not the usual foreground/background tokens, matching the
// reference exactly — this mark intentionally does not adapt to light/dark
// site theme (same fixed-color treatment as the "Get started" button and
// hero chat mockup elsewhere on this page).
//
// Exported so PipelineDiagram can redraw the identical mark inline (as
// a <g transform>) at the center of the hero diagram, instead of nesting a
// second <svg> via foreignObject.
export const BRAIN_OUTER_PATH =
  "M35 15 C20 15 12 28 14 40 C6 44 4 58 12 66 C10 76 18 86 30 86 C33 92 42 94 48 90 C54 94 63 92 66 86 C78 86 86 76 84 66 C92 58 90 44 82 40 C84 28 76 15 61 15 C56 10 44 10 39 15 C37 14 37 14 35 15 Z M50 20 L50 88";

export const BRAIN_LINE_PATHS = [
  { d: "M50 25 C46 30 44 36 48 40 C44 44 44 50 48 54 C43 57 43 63 48 66 C44 70 46 76 50 80", strokeWidth: 3 },
  { d: "M38 22 C33 26 30 32 33 38", strokeWidth: 2.5 },
  { d: "M62 22 C67 26 70 32 67 38", strokeWidth: 2.5 },
  { d: "M25 45 C20 48 19 54 23 58", strokeWidth: 2.5 },
  { d: "M75 45 C80 48 81 54 77 58", strokeWidth: 2.5 },
  { d: "M22 68 C24 73 29 76 34 75", strokeWidth: 2.5 },
  { d: "M78 68 C76 73 71 76 66 75", strokeWidth: 2.5 },
];

// `inverted` swaps fill/stroke (white silhouette, black lines) for use on a
// dark chip/badge (e.g. the app sidebar's black logo square) — same exact
// path data either way, per the approved reference.
export default function BrainMark({ size = 20, className = "", inverted = false }) {
  const fill = inverted ? "#FFFFFF" : "#000000";
  const stroke = inverted ? "#000000" : "#FFFFFF";
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" className={className} aria-hidden="true">
      <path d={BRAIN_OUTER_PATH} fill={fill} />
      {BRAIN_LINE_PATHS.map(({ d, strokeWidth }) => (
        <path key={d} d={d} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" />
      ))}
    </svg>
  );
}
