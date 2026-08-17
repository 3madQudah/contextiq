import { useEffect, useId, useState } from "react";

import { BRAIN_LINE_PATHS, BRAIN_OUTER_PATH } from "./landing/BrainMark.jsx";

// Fan-in pipeline diagram for the Landing hero: six source file types
// converge on the brain hub, which emits one cited answer. Replaces the
// previous hub-and-spoke diagram (radial burst, brain floating in the
// middle of a ring of file-type nodes) with a left-to-right "sources ->
// retrieval -> answer" read.
//
// Captions are verified against the codebase, same rule Landing.jsx already
// applies to FEATURES/HERO_BULLETS — used verbatim, not paraphrased:
//   DOCX   -> loaders/document_loader.py load_docx_by_section()
//   PDF    -> loaders/document_loader.py load_pdf_with_scan_detection()
//   MD     -> loaders/document_loader.py load_md_by_section()
//   TXT    -> prompt_eng/txt_prompt.py TXT_GUIDANCE
//   CSV    -> chain/csv_compute.py module docstring
//   SQL DB -> chain/sql_chain.py module docstring
const SOURCES = [
  {
    id: "docx",
    label: "DOCX",
    desc: "Loaded section by section, so answers stay scoped to the right heading instead of blurring sections together.",
  },
  {
    id: "pdf",
    label: "PDF",
    desc: "Read page by page — scanned PDFs with no extractable text layer are rejected at upload, not silently indexed empty.",
  },
  {
    id: "md",
    label: "MD",
    desc: "Loaded by header hierarchy, so headers and code fences stay real structure instead of flattened text.",
  },
  {
    id: "txt",
    label: "TXT",
    desc: "No headings to lean on, so answers draw on the surrounding sentences within each retrieved chunk.",
  },
  {
    id: "csv",
    label: "CSV",
    desc: "Aggregation questions skip retrieval entirely — pandas computes the exact answer over the full uploaded file.",
  },
  {
    id: "sql",
    label: "SQL DB",
    desc: "A separate text-to-SQL path writes one read-only SELECT, validated and run with a statement timeout.",
  },
];

const CYCLE_MS = 5000;

// Desktop (>= md): six pills fan into the hub at (320, 200), which feeds a
// single output line into the answer card.
const DESKTOP_VIEWBOX = "0 0 680 400";
const DESKTOP_PILL_Y = [43, 99, 155, 211, 267, 323];
const DESKTOP_HUB = { x: 320, y: 200 };
const DESKTOP_CONNECTORS = [
  "M152,60 C200,60 228,200 276,200",
  "M152,116 C200,116 228,200 276,200",
  "M152,172 C200,172 228,200 276,200",
  "M152,228 C200,228 228,200 276,200",
  "M152,284 C200,284 228,200 276,200",
  "M152,340 C200,340 228,200 276,200",
];
const DESKTOP_OUTPUT = "M364,200 H422";
const DESKTOP_CARD = { x: 430, y: 170, w: 200, h: 60 };

// Mobile (< md): same six sources in a row across the top, hub in the
// middle, answer card at the bottom — shortened verticals fan into the hub
// instead of the desktop's long horizontal beziers.
const MOBILE_VIEWBOX = "0 0 360 470";
const MOBILE_PILL_X = [40, 96, 152, 208, 264, 320];
const MOBILE_HUB = { x: 180, y: 250 };
const MOBILE_CONNECTORS = [
  "M40,50 C40,140 180,160 180,210",
  "M96,50 C96,140 180,160 180,210",
  "M152,50 C152,140 180,160 180,210",
  "M208,50 C208,140 180,160 180,210",
  "M264,50 C264,140 180,160 180,210",
  "M320,50 C320,140 180,160 180,210",
];
const MOBILE_OUTPUT = "M180,290 V390";
const MOBILE_CARD = { x: 80, y: 390, w: 200, h: 60 };

// Pill/card label sizes, in SVG user units. Desktop's viewBox (680 wide) is
// rendered inside a column that tops out at 552px (the hero grid's
// structural ceiling with the copy column held at its own max-w-lg floor —
// see Landing.jsx), a ~0.81x scale — so 14-unit text (the "14px" called for
// in the design) would render at ~11.4px, just under this app's 11.5px text
// floor (tailwind.config.js `2xs`). Bumped to 15 here to clear it with
// margin (~12.2px); the muted card subtitle is bumped less (12 -> 13,
// ~10.6px rendered) since it's secondary text, not primary content.
// Mobile's viewBox (360 wide) renders close to 1:1 and keeps original sizes.
const DESKTOP_TEXT = { pillLabel: 15, cardTitle: 15, cardSub: 13 };
const MOBILE_TEXT = { pillLabel: 14, cardTitle: 14, cardSub: 12 };

// Per-pulse stagger so the six traveling dashes arrive at the hub in
// sequence rather than all at once; the output pulse gets its own delay and
// accent color (success, not accent) so it visually reads as "the answer
// leaving" rather than a seventh input.
const PULSE_DELAYS = [0, 0.36, 0.72, 1.08, 1.44, 1.8];
const OUTPUT_PULSE_DELAY = 1;

// Active-source indication lives entirely on the pulse now — the pills
// themselves are visually static (see the pills render block below). The
// active pulse runs faster (shorter animation-duration) in addition to
// being fuller-opacity/thicker, so switching sources reads as "this one
// speeds up," not just a color swap.
const PULSE_DURATION_S = 2.2; // matches tailwind.config.js's pipeline-flow base duration
const ACTIVE_PULSE_DURATION_S = 1.3;

// Entrance choreography: connectors draw in first (staggered 0.06s apart,
// 0.7s each — the output line is treated as a 7th connector so pills wait
// for it too), pills fade/slide in after, answer card last. Derived from
// the stagger constant rather than hand-picked so the three phases can
// never drift out of sync if SOURCES grows.
//
// Pure CSS (see tailwind.config.js's pipeline-line-in/pill-in/card-in +
// index.css), not Framer's whileInView — deliberately. whileInView needs
// IntersectionObserver on the SVG children, which has real gaps on WebKit/
// Safari (confirmed: this exact diagram, driven by Framer, silently never
// left its "hidden" initial state in Safari, even though the identical
// propagation logic is proven fine elsewhere in this app and reproduces
// fine in both Chromium and Playwright's WebKit engine — evidence points
// at Safari's IntersectionObserver-on-SVG specifically, not the animation
// library or reduced motion). Every element below carries its plain,
// un-gated, already-correct resting attribute/style as the base value
// (strokeDashoffset={0}, natural opacity 1, no transform) — the CSS
// `@keyframes` only ever TEMPORARILY overrides that via `animation-fill-
// mode: both`. If the animation fails to apply for any reason (this
// mechanism, a future one, JS disabled entirely), the element still
// renders its correct final appearance — visibility is never contingent
// on the animation succeeding. Same property as the reduced-motion guard
// in index.css, which now just disables the `animation`, no extra
// opacity override needed, since "no animation" already means "final
// state, immediately."
const LINE_STAGGER = 0.06;
const OUTPUT_LINE_DELAY = SOURCES.length * LINE_STAGGER;
const PILLS_START = (SOURCES.length + 1) * LINE_STAGGER;
const CARD_START = PILLS_START + SOURCES.length * LINE_STAGGER;

// Tracks whether the viewport is at/above Tailwind's `md` breakpoint so the
// component can switch its viewBox/path set in JS rather than shipping two
// SVGs and letting CSS hide one (which would leave an off-screen copy
// animating for no reason, entrance included).
function useIsDesktop() {
  const query = "(min-width: 768px)";
  const [isDesktop, setIsDesktop] = useState(
    () => typeof window !== "undefined" && window.matchMedia(query).matches
  );

  useEffect(() => {
    const mql = window.matchMedia(query);
    const onChange = (e) => setIsDesktop(e.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return isDesktop;
}

export default function PipelineDiagram({ className = "" }) {
  const isDesktop = useIsDesktop();
  const descId = useId();

  const [autoIndex, setAutoIndex] = useState(0);
  const [lockedIndex, setLockedIndex] = useState(null);
  const activeIndex = lockedIndex ?? autoIndex;
  const active = SOURCES[activeIndex];

  // Auto-cycle the caption; paused (not reset) while a pill is hovered/focused.
  useEffect(() => {
    if (lockedIndex !== null) return;
    const id = setInterval(() => setAutoIndex((i) => (i + 1) % SOURCES.length), CYCLE_MS);
    return () => clearInterval(id);
  }, [lockedIndex]);

  const viewBox = isDesktop ? DESKTOP_VIEWBOX : MOBILE_VIEWBOX;
  const connectors = isDesktop ? DESKTOP_CONNECTORS : MOBILE_CONNECTORS;
  const outputPath = isDesktop ? DESKTOP_OUTPUT : MOBILE_OUTPUT;
  const hub = isDesktop ? DESKTOP_HUB : MOBILE_HUB;
  const card = isDesktop ? DESKTOP_CARD : MOBILE_CARD;
  const pillPositions = isDesktop
    ? DESKTOP_PILL_Y.map((y) => ({ x: 48, y, w: 104, h: 34, labelX: 100, labelY: y + 17 }))
    : MOBILE_PILL_X.map((cx) => ({ x: cx - 26, y: 20, w: 52, h: 30, labelX: cx, labelY: 35 }));
  const text = isDesktop ? DESKTOP_TEXT : MOBILE_TEXT;

  return (
    <div className={className}>
      <svg
        width="100%"
        viewBox={viewBox}
        role="img"
        aria-label="ContextIQ retrieval pipeline"
        aria-describedby={descId}
        className="overflow-visible"
      >
        {/* Not <title> — a native SVG <title> renders as a browser hover
            tooltip, which showed up as an unwanted floating label near the
            hub. aria-label covers the short name; <desc> (referenced via
            aria-describedby, which does NOT trigger a tooltip) covers the
            longer description. */}
        <desc id={descId}>
          Six source types — Word documents, PDFs, Markdown, plain text, CSV, and SQL databases —
          feed into ContextIQ's hybrid retrieval, which returns one answer with inline citations.
        </desc>

        {/* Entrance: connectors draw in, then pills, then the answer card. */}
        <g>
          {connectors.map((d, i) => (
            <path
              key={SOURCES[i].id}
              d={d}
              fill="none"
              pathLength={100}
              strokeDasharray="100 100"
              strokeDashoffset={0}
              className="stroke-border/40 animate-pipeline-line-in"
              strokeWidth={1}
              style={{ animationDelay: `${i * LINE_STAGGER}s` }}
            />
          ))}
          <path
            d={outputPath}
            fill="none"
            pathLength={100}
            strokeDasharray="100 100"
            strokeDashoffset={0}
            className="stroke-border/40 animate-pipeline-line-in"
            strokeWidth={1}
            style={{ animationDelay: `${OUTPUT_LINE_DELAY}s` }}
          />

          {/* Traveling pulses: plain (non-motion) duplicate paths, animated
              by pure CSS keyframes (see index.css / tailwind.config.js) so
              an infinite loop never depends on Framer keeping a JS
              animation frame alive. This is now the ONLY place isActive
              touches appearance — the active pulse is fuller-opacity,
              thicker, and visibly faster; the rest stay clearly visible but
              quieter. transition-all smooths the opacity/stroke-width jump
              when the active source changes; animation-duration itself
              isn't transitioned (not meaningfully transitionable), so the
              speed change lands immediately. */}
          {connectors.map((d, i) => {
            const isActive = i === activeIndex;
            return (
              <path
                key={`pulse-${SOURCES[i].id}`}
                d={d}
                fill="none"
                pathLength={100}
                strokeDasharray="8 100"
                strokeLinecap="round"
                className="pipeline-pulse animate-pipeline-flow stroke-accent transition-all duration-300"
                strokeWidth={isActive ? 3 : 1.5}
                style={{
                  animationDelay: `${PULSE_DELAYS[i]}s`,
                  animationDuration: `${isActive ? ACTIVE_PULSE_DURATION_S : PULSE_DURATION_S}s`,
                  opacity: isActive ? 1 : 0.35,
                }}
              />
            );
          })}
          <path
            d={outputPath}
            fill="none"
            pathLength={100}
            strokeDasharray="8 100"
            strokeLinecap="round"
            className="pipeline-pulse animate-pipeline-flow stroke-success"
            strokeWidth={2}
            style={{ animationDelay: `${OUTPUT_PULSE_DELAY}s` }}
          />

          {/* Hub: reuses the existing brain mark (see BrainMark.jsx) — same
              fixed black/white treatment as the nav/sidebar mark, not
              theme-adaptive. Ripple sits behind it; both loop via CSS. The
              static translate+scale below (SVG `transform` attribute)
              positions/sizes the brain once; the CSS breathing animation is
              applied to an inner <g> with no attribute of its own, since a
              CSS `transform` on the same element would replace — not
              compose with — that attribute. */}
          <circle
            cx={hub.x}
            cy={hub.y}
            r={44}
            fill="none"
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
            className="pipeline-ripple animate-pipeline-ripple stroke-accent"
          />
          <g transform={`translate(${hub.x - 40}, ${hub.y - 40}) scale(0.8)`}>
            <g className="pipeline-hub-breathe animate-pipeline-hub">
              <path d={BRAIN_OUTER_PATH} fill="#000000" />
              {BRAIN_LINE_PATHS.map(({ d, strokeWidth }) => (
                <path key={d} d={d} fill="none" stroke="#FFFFFF" strokeWidth={strokeWidth} strokeLinecap="round" />
              ))}
            </g>
          </g>

          {/* Source pills — visually identical at all times, deliberately.
              An earlier version changed a pill's own fill/border/label on
              hover/active, and cycling that color read as distracting.
              Active-source indication now lives entirely on the pulse
              (above); nothing here reads `activeIndex` or `isActive` at
              all. Hover/focus still lock the caption and drive which pulse
              is emphasized — see the handlers below — only the pill's own
              appearance stops responding to it. */}
          {SOURCES.map((source, i) => {
            const pos = pillPositions[i];
            return (
              <g
                key={source.id}
                className="animate-pipeline-pill-in"
                style={{ animationDelay: `${PILLS_START + i * LINE_STAGGER}s` }}
              >
                <g
                  tabIndex={0}
                  role="button"
                  aria-label={`${source.label}: ${source.desc}`}
                  className="cursor-pointer outline-none"
                  onMouseEnter={() => setLockedIndex(i)}
                  onMouseLeave={() => setLockedIndex(null)}
                  onFocus={() => setLockedIndex(i)}
                  onBlur={() => setLockedIndex(null)}
                >
                  <rect
                    x={pos.x}
                    y={pos.y}
                    width={pos.w}
                    height={pos.h}
                    rx={8}
                    className="fill-pipeline-surface stroke-pipeline-border"
                    strokeWidth={0.5}
                  />
                  <text
                    x={pos.labelX}
                    y={pos.labelY}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize={text.pillLabel}
                    fontWeight={500}
                    className="fill-pipeline-label"
                  >
                    {source.label}
                  </text>
                </g>
              </g>
            );
          })}

          {/* Answer card */}
          <g className="animate-pipeline-card-in" style={{ animationDelay: `${CARD_START}s` }}>
            <rect x={card.x} y={card.y} width={card.w} height={card.h} rx={12} className="fill-success/10 stroke-success" strokeWidth={0.5} />
            <text
              x={card.x + card.w / 2}
              y={card.y + card.h / 2 - 9}              textAnchor="middle"
              dominantBaseline="central"
              fontSize={text.cardTitle}
              fontWeight={500}
              className="fill-success"
            >
              Answer
            </text>
            <text
              x={card.x + card.w / 2}
              y={card.y + card.h / 2 + 9}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={text.cardSub}
              className="fill-muted"
            >
              With inline citations
            </text>
          </g>
        </g>
      </svg>

      {/* Reserves 2 lines (min-h-9, 36px) at text-sm's 18px line-height from
          `sm` up, where all six captions measure 2 lines at every tested
          width (420px-1400px). Below `sm`, real phone widths (375px etc.)
          push all six to 3 lines — min-h-14 (56px; the scale has no 54px
          step, so this rounds up rather than adding a bracket literal)
          covers that. Checked live across all six sources at 11 widths:
          the 3-to-2-line crossover lands at the same width for every one
          of them (400px -> 420px), so there's no width where different
          captions disagree and shift against each other — only the two
          breakpoint bands above, which is what's reserved for here. */}
      <p className="mt-3 min-h-14 text-center text-sm sm:min-h-9" aria-live="polite">
        <span className="font-medium text-foreground">{active.label}</span>
        <span className="text-muted"> — {active.desc}</span>
      </p>
    </div>
  );
}
