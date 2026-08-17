import { motion } from "motion/react";

import { easeOut } from "../../lib/motion.js";

// Shared numbered-step layout for /product and /databases — same card
// treatment (glass panel, badge, title, body) so both content pages read
// as one family instead of each inventing its own list style. The badge
// itself diverges per page: Product uses a bold number (the "which step
// is this" anchor), Databases passes a per-step `icon` instead — a square
// accent badge matching the landing page's feature-card icon treatment.
const container = {
  initial: {},
  animate: { transition: { staggerChildren: 0.09 } },
};
const item = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.45, ease: easeOut } },
};

export default function StepList({ steps }) {
  return (
    <motion.ol
      initial="initial"
      whileInView="animate"
      viewport={{ once: true, margin: "-60px" }}
      variants={container}
      className="flex flex-col gap-4"
    >
      {steps.map((step, i) => (
        <motion.li
          key={step.title}
          variants={item}
          className="glass-panel flex gap-4 rounded-xl border border-border p-5 sm:p-6"
        >
          {step.icon ? (
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
              <step.icon size={16} stroke={1.75} />
            </div>
          ) : (
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent/10 text-lg font-bold text-accent">
              {i + 1}
            </div>
          )}
          <div className="min-w-0">
            <h3 className="text-base font-semibold text-foreground">{step.title}</h3>
            <p className="mt-1.5 text-sm text-muted">{step.body}</p>
            {step.note && <p className="mt-2 text-xs text-muted">{step.note}</p>}
          </div>
        </motion.li>
      ))}
    </motion.ol>
  );
}
