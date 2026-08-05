import { motion } from "framer-motion";
import {
  ChevronRight,
  FileSearch,
  Github,
  Layers,
  Lock,
  MessageCircle,
  UploadCloud,
} from "lucide-react";
import { Link } from "react-router-dom";

import Button from "../components/Button.jsx";
import Logo from "../components/Logo.jsx";
import ThemeToggle from "../components/ThemeToggle.jsx";

const FEATURES = [
  {
    icon: Layers,
    title: "Hybrid retrieval",
    body: "Combines vector similarity and keyword matching, so exact numbers and rare terms are never missed.",
  },
  {
    icon: FileSearch,
    title: "Cited answers",
    body: "Every answer names the exact file it came from, so you can verify it yourself.",
  },
  {
    icon: Lock,
    title: "Private by default",
    body: "Your documents and conversations are isolated to your account alone.",
  },
];

const STEPS = [
  { icon: UploadCloud, title: "Upload", body: "Drop in PDFs, docs, spreadsheets, or notes." },
  { icon: Layers, title: "Index", body: "Chunked, embedded, and indexed for hybrid search." },
  { icon: MessageCircle, title: "Ask", body: "Get grounded answers with sources, in plain English." },
];

const fadeUp = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
};

export default function Landing() {
  return (
    <div className="min-h-screen bg-bg">
      <nav className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
        <Logo />
        <div className="flex items-center gap-1">
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            aria-label="GitHub repository"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted hover:bg-surface-hover hover:text-foreground"
          >
            <Github size={16} strokeWidth={1.5} />
          </a>
          <ThemeToggle />
          <Link
            to="/login"
            className="ml-2 px-3 py-2 text-sm text-muted hover:text-foreground"
          >
            Log in
          </Link>
          <Link to="/register">
            <Button variant="primary" className="text-sm">
              Get started
            </Button>
          </Link>
        </div>
      </nav>

      <header className="mx-auto flex max-w-3xl flex-col items-center px-6 pb-24 pt-16 text-center">
        <motion.div
          initial={fadeUp.initial}
          animate={fadeUp.animate}
          transition={{ duration: 0.18 }}
          className="mb-5 inline-flex items-center rounded-full border border-border px-3 py-1 text-xs text-muted"
        >
          Hybrid retrieval — FAISS + BM25, not just embeddings
        </motion.div>

        <motion.h1
          initial={fadeUp.initial}
          animate={fadeUp.animate}
          transition={{ duration: 0.18, delay: 0.04 }}
          className="text-xl font-medium leading-snug text-foreground sm:text-2xl"
        >
          Chat with your own documents.
        </motion.h1>

        <motion.p
          initial={fadeUp.initial}
          animate={fadeUp.animate}
          transition={{ duration: 0.18, delay: 0.08 }}
          className="mt-4 max-w-lg text-base text-muted"
        >
          Upload PDFs, spreadsheets, and notes. ContextIQ combines semantic search and
          keyword matching to answer questions with exact citations — not guesses.
        </motion.p>

        <motion.div
          initial={fadeUp.initial}
          animate={fadeUp.animate}
          transition={{ duration: 0.18, delay: 0.12 }}
          className="mt-8 flex items-center gap-3"
        >
          <Link to="/register">
            <Button variant="primary">Get started</Button>
          </Link>
          <Link to="/login">
            <Button variant="secondary">Log in</Button>
          </Link>
        </motion.div>

        <p className="mt-4 text-sm text-muted">Free · no credit card</p>
      </header>

      <section className="border-y border-border">
        <div className="mx-auto grid max-w-5xl grid-cols-1 divide-y divide-border sm:grid-cols-3 sm:divide-x sm:divide-y-0">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <div key={title} className="flex flex-col gap-2 px-8 py-10">
              <Icon size={18} strokeWidth={1.5} className="text-muted" />
              <h3 className="text-base font-medium text-foreground">{title}</h3>
              <p className="text-sm text-muted">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-6 py-20">
        <h2 className="mb-10 text-center text-base font-medium text-muted">How it works</h2>
        <div className="flex flex-col items-stretch gap-6 sm:flex-row sm:items-center sm:justify-between sm:gap-2">
          {STEPS.map(({ icon: Icon, title, body }, i) => (
            <div key={title} className="flex flex-1 items-center gap-2">
              <div className="flex flex-1 flex-col items-center gap-2 text-center">
                <div
                  className={`flex h-9 w-9 items-center justify-center rounded-md border ${
                    i === STEPS.length - 1
                      ? "border-accent/30 bg-accent/10 text-accent"
                      : "border-border text-muted"
                  }`}
                >
                  <Icon size={16} strokeWidth={1.5} />
                </div>
                <p className="text-base font-medium text-foreground">{title}</p>
                <p className="max-w-[160px] text-sm text-muted">{body}</p>
              </div>
              {i < STEPS.length - 1 && (
                <ChevronRight
                  size={16}
                  strokeWidth={1.5}
                  className="hidden shrink-0 text-muted sm:block"
                />
              )}
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-2 px-6 py-8 text-sm text-muted sm:flex-row">
          <p>FastAPI · FAISS · BM25 · LangChain · React</p>
          <p>Emad Al-Qadah</p>
        </div>
      </footer>
    </div>
  );
}
