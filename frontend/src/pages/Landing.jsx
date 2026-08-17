import {
  IconCheck,
  IconLayersIntersect,
  IconLock,
  IconQuote,
  IconShieldLock,
} from "@tabler/icons-react";
import { motion } from "motion/react";
import { Link } from "react-router-dom";

import ChatMockup from "../components/landing/ChatMockup.jsx";
import PipelineDiagram from "../components/PipelineDiagram.jsx";
import PublicFooter from "../components/landing/PublicFooter.jsx";
import PublicNav from "../components/landing/PublicNav.jsx";
import Button from "../components/Button.jsx";
import { easeOut } from "../lib/motion.js";

// Copy verified against the codebase (see hybrid_retriever.py, rag_chain.py,
// vector_store.py/keyword_store.py, crypto.py/db_connection_models.py,
// sql_chain.py) — used verbatim, not paraphrased.
const FEATURES = [
  {
    icon: IconLayersIntersect,
    title: "Hybrid retrieval",
    body: "Combines keyword search (BM25) and semantic search (FAISS) with equal weighting, so exact numbers, codes, and rare terms are never missed by vector search alone.",
  },
  {
    icon: IconQuote,
    title: "Cited answers",
    body: "Every answer names the exact source file it came from, so you can verify it against the original document yourself.",
  },
  {
    icon: IconLock,
    title: "Private by default",
    body: "Documents, conversations, and search indexes are isolated per account — nothing is ever shared or mixed between users.",
  },
  {
    icon: IconShieldLock,
    title: "Encrypted connections",
    body: "Database connection strings are encrypted at rest and never returned by the API — read-only access enforced at the query and connection level.",
  },
];

// Verified against the codebase — same rule as FEATURES above:
//   1. chain/query_rewriter.py rewrite_query() + chain/rag_chain.py's use of
//      conversation history before retrieval.
//   2. chain/csv_compute.py — bypasses retrieval entirely for aggregation
//      questions, loads the full uploaded CSV via pandas, computes exact
//      sum/mean/median/etc. (never a chunked/partial sample).
//   3. Per-file-type classifier + compute + prompt modules (chain/*_compute.py,
//      chain/*_query_classifier.py, prompt_eng/*_prompt.py) selected per
//      chunk.metadata["file_type"] in rag_chain.py/chat_routes.py.
const HERO_BULLETS = [
  {
    label: "Remembers the conversation",
    body: 'follow-up questions like "what about last quarter?" resolve correctly using your chat history.',
  },
  {
    label: "Real math, not estimates",
    body: "spreadsheet totals and averages are computed directly on your full data, never guessed from a partial sample.",
  },
  {
    label: "Tuned per file type",
    body: "PDFs, spreadsheets, and structured documents are each handled with logic built for how that format actually behaves.",
  },
];

// Hero left-column entrance: headline -> paragraph -> bullets -> CTA, ~130ms
// apart (the outer heroContainer stagger below positions this block as a
// whole); bulletsContainer/bulletItem then stagger the 3 bullets within it,
// ~110ms apart, once the block itself starts animating.
const heroContainer = {
  initial: {},
  animate: { transition: { staggerChildren: 0.13, delayChildren: 0.05 } },
};
const heroItem = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.6, ease: easeOut } },
};

const bulletsContainer = {
  initial: {},
  animate: { transition: { staggerChildren: 0.11 } },
};
const bulletItem = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: easeOut } },
};

const cardsContainer = {
  initial: {},
  animate: { transition: { staggerChildren: 0.1 } },
};
const cardItem = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: easeOut } },
};

// Mirrors claims already verified above (FEATURES/HERO_BULLETS) — same 4
// ideas from the codebase, phrased as a step-by-step pipeline instead of
// standalone claims.
const DEMO_STEPS = [
  { title: "Ingest", body: "Parsed per file type, not one generic loader." },
  { title: "Chunk and embed", body: "Stored in an index that is yours alone." },
  { title: "Retrieve", body: "Semantic and keyword search, combined." },
  { title: "Generate", body: "Answered only from what was actually found." },
];

// Outer stagger: steps-block, then the chat card (~0.15s later, so it
// visibly trails rather than arriving mid-sequence) — the connector column
// in between is a plain (non-motion) div, so it doesn't consume a stagger
// slot. Inner stagger: the 4 steps themselves, ~0.08s apart. Reduced motion
// is handled globally by <MotionConfig reducedMotion="user"> in main.jsx,
// same as every other animation on this page — nothing extra needed here.
const demoOuterContainer = {
  initial: {},
  animate: { transition: { staggerChildren: 0.15 } },
};
const demoStepsContainer = {
  initial: {},
  animate: { transition: { staggerChildren: 0.08 } },
};
const demoStepItem = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: easeOut } },
};
const demoChatItem = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: easeOut } },
};

export default function Landing() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-bg">
      <PublicNav />

      {/* Right column is `1fr` against a left column pinned to `32rem`
          (512px) — the copy's own max-w-lg paragraph is the real width
          floor for the left side, so rather than a symmetric 50/50 split
          (which caps both columns at 520px at this container's widest),
          the left column gets exactly what its content needs and the
          diagram column gets whatever's left: 552px at full container
          width (1104px content - 512px left - 40px gap). Gap trimmed from
          16 to 10 to help reclaim that width without visually crowding the
          boundary between the copy and the diagram's pills. */}
      <header className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-8 px-6 pb-10 pt-8 lg:grid-cols-[minmax(0,32rem)_1fr] lg:gap-10 lg:pb-14 lg:pt-10">
        <motion.div initial="initial" animate="animate" variants={heroContainer}>
          <motion.h1 variants={heroItem} className="text-xl font-medium text-foreground">
            Your documents, finally ready to answer back.
          </motion.h1>

          <motion.p variants={heroItem} className="mt-3 max-w-lg text-md text-muted">
            ContextIQ is a full-stack RAG system that lets you upload PDFs, spreadsheets, and
            documents or connect a live database, then ask questions in plain English. It
            combines semantic and keyword search to find exact answers, not guesses, and every
            response cites the file it came from.
          </motion.p>

          <motion.div variants={bulletsContainer} className="mt-5 flex flex-col gap-3">
            {HERO_BULLETS.map(({ label, body }) => (
              <motion.div key={label} variants={bulletItem} className="flex items-start gap-2.5">
                <span className="mt-0.5 flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full bg-accent/10 text-accent">
                  <IconCheck size={11} stroke={2.5} />
                </span>
                <p className="text-sm text-muted">
                  <span className="font-semibold text-foreground">{label}</span> — {body}
                </p>
              </motion.div>
            ))}
          </motion.div>

          <motion.div variants={heroItem} className="mt-5">
            <Link to="/register">
              <Button variant="invert">Get started</Button>
            </Link>
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="w-full justify-self-center lg:justify-self-end"
        >
          <PipelineDiagram className="w-full" />
        </motion.div>
      </header>

      {/* Demo band: full-width bg-surface tint so it reads as a distinct
          section. */}
      <section className="bg-surface">
        <div className="mx-auto max-w-6xl px-6 py-12 lg:py-16">
          <motion.h2
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5, ease: easeOut }}
            className="text-center text-lg font-semibold text-foreground"
          >
            Ask a question, get a cited answer
          </motion.h2>

          <motion.div
            initial="initial"
            whileInView="animate"
            viewport={{ once: true, margin: "-80px" }}
            variants={demoOuterContainer}
            className="mt-10 grid grid-cols-1 items-center gap-12 lg:grid-cols-[1fr_48px_1.1fr] lg:gap-8"
          >
            {/* LEFT: 4-step pipeline */}
            <motion.div variants={demoStepsContainer}>
              {DEMO_STEPS.map((step, i) => {
                const isLast = i === DEMO_STEPS.length - 1;
                return (
                  <motion.div key={step.title} variants={demoStepItem} className="flex gap-3">
                    <div className="flex shrink-0 flex-col items-center">
                      <span className="flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full bg-accent/10 text-2xs font-semibold text-accent">
                        {i + 1}
                      </span>
                      {/* Step-to-step connector, centered under the circle. */}
                      {!isLast && <span aria-hidden="true" className="w-px flex-1 bg-border" />}
                    </div>
                    <div className={isLast ? "" : "pb-6"}>
                      <h3 className="text-sm font-medium text-foreground">{step.title}</h3>
                      <p className="text-xs text-muted">{step.body}</p>
                    </div>
                  </motion.div>
                );
              })}

              {/* Mobile-only stand-in for the lg connector column: a short
                  downward arrow between the steps block and the chat card
                  once they stack to a single column. */}
              <div aria-hidden="true" className="flex justify-center pt-2 lg:hidden">
                <svg width="7" height="7" viewBox="0 0 7 7">
                  <polygon points="0,0 7,0 3.5,7" className="fill-border" />
                </svg>
              </div>
            </motion.div>

            {/* MIDDLE: step-4 -> chat connector, lg only. A dedicated grid
                column (not absolute positioning) so it self-centers via
                items-center against the row's height — no hardcoded
                offsets to keep in sync with the steps' variable height. */}
            <div aria-hidden="true" className="hidden lg:flex lg:items-center lg:justify-center">
              <span className="h-px w-8 bg-border" />
              <svg width="7" height="7" viewBox="0 0 7 7" className="shrink-0">
                <polygon points="0,0 7,3.5 0,7" className="fill-border" />
              </svg>
            </div>

            {/* RIGHT: chat mockup, unchanged content, slightly larger (see
                ChatMockup.jsx: max-w-[348px] -> max-w-[380px]) */}
            <motion.div variants={demoChatItem} className="flex justify-center lg:justify-start">
              <ChatMockup />
            </motion.div>
          </motion.div>
        </div>
      </section>

      <section className="border-y border-border">
        {/* Own px-6 container, separate from the grid below: the grid is
            deliberately full-bleed (no horizontal padding of its own) below
            max-w-6xl, unchanged from before — only the heading needs a
            viewport gutter. */}
        <div className="mx-auto max-w-6xl px-6 pt-12 lg:pt-16">
          <motion.h2
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5, ease: easeOut }}
            className="text-center text-lg font-semibold text-foreground"
          >
            Built for answers you can check
          </motion.h2>
        </div>
        <motion.div
          initial="initial"
          whileInView="animate"
          viewport={{ once: true, margin: "-80px" }}
          variants={cardsContainer}
          className="mx-auto mt-6 grid max-w-6xl grid-cols-1 gap-px bg-border sm:grid-cols-2 lg:grid-cols-4"
        >
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <motion.div key={title} variants={cardItem} className="group bg-bg px-6 py-8">
              <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 text-accent transition-transform duration-200 group-hover:-rotate-[4deg] group-hover:scale-[1.08]">
                <Icon size={15} stroke={1.75} />
              </div>
              <h3 className="text-sm font-semibold text-foreground">{title}</h3>
              <p className="mt-1.5 text-2xs text-muted">{body}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <PublicFooter />
    </div>
  );
}
