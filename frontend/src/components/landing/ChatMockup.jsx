// Static browser-chrome-style mockup of a ContextIQ chat exchange, shown in
// the "Ask a question, get a cited answer" demo band on Landing. Purely
// decorative/illustrative — not wired to the real Composer/MessageBubble
// components, since it needs to render one fixed sample conversation
// regardless of app state.
//
// Colors here are fixed literals rather than the usual surface/foreground
// tokens — a deliberate corrective spec, so unlike the rest of the page
// this card intentionally does not adapt to light/dark site theme. Per the
// approved reference: neutral gray chrome (border, divider, traffic-light
// dots) with color reserved for exactly two things — the pale-blue question
// bubble and the blue chip outlines/text, both the same calm blue-700/50/300
// family. The answer paragraph is black, not blue.
//
// max-w-[380px] (bumped from the original 348px so the card reads as
// slightly larger next to the demo section's 4-step pipeline). Internal
// padding/font sizes are NOT rescaled to match — those stay at their
// original arbitrary px values, so the card gains a bit more edge
// breathing room rather than a fully proportional resize.
export default function ChatMockup({ className = "" }) {
  return (
    <div
      className={`w-full max-w-[380px] overflow-hidden rounded-xl border border-gray-200 bg-white shadow-glass ${className}`}
    >
      <div className="flex items-center gap-[7px] border-b border-gray-200 px-[15px] py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-gray-300" />
        <span className="h-2.5 w-2.5 rounded-full bg-gray-300" />
        <span className="h-2.5 w-2.5 rounded-full bg-gray-300" />
      </div>

      <div className="flex flex-col gap-3 px-[15px] py-[15px]">
        <div className="flex justify-end">
          <div className="max-w-[85%] rounded-lg bg-blue-50 px-3 py-[7px] text-[17px] text-blue-700">
            Which region drove the Q3 revenue jump?
          </div>
        </div>

        <div className="max-w-[90%]">
          <p className="text-[17px] text-black">
            NA revenue grew 34% quarter-over-quarter, driven mainly by enterprise renewals.
          </p>
          <div className="mt-2.5 flex flex-wrap gap-[7px]">
            <span className="inline-flex items-center gap-1 rounded-full border border-blue-300 bg-transparent px-2.5 py-0.5 text-[15px] leading-none text-blue-700">
              q3-report.pdf
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-blue-300 bg-transparent px-2.5 py-0.5 text-[15px] leading-none text-blue-700">
              sales.csv
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
