import { motion } from "motion/react";

import PublicFooter from "../../components/landing/PublicFooter.jsx";
import PublicNav from "../../components/landing/PublicNav.jsx";
import { easeOut } from "../../lib/motion.js";

// Endpoint list extracted directly from backend/api/*.py + main.py's
// app.include_router(...) prefixes — every method/path/description below
// matches the actual route declarations, not a guessed or aspirational API.
const ENDPOINT_GROUPS = [
  {
    name: "Auth",
    endpoints: [
      { method: "POST", path: "/api/auth/register", desc: "Create a new account." },
      {
        method: "POST",
        path: "/api/auth/login",
        desc: "Authenticate with email/password and receive a JWT access token.",
      },
    ],
  },
  {
    name: "Documents",
    endpoints: [
      {
        method: "POST",
        path: "/api/documents/upload",
        desc: "Upload a file and ingest it — chunk, embed, and index it into your hybrid search.",
      },
      { method: "GET", path: "/api/documents/", desc: "List your uploaded documents." },
      {
        method: "DELETE",
        path: "/api/documents/{file_name}",
        desc: "Delete a document and rebuild your search indexes without it.",
      },
    ],
  },
  {
    name: "Chat",
    endpoints: [
      {
        method: "POST",
        path: "/api/chat/ask",
        desc: "Ask a question against your document index and get a cited answer.",
      },
    ],
  },
  {
    name: "Conversations",
    endpoints: [
      { method: "GET", path: "/api/conversations", desc: "List your conversations." },
      { method: "POST", path: "/api/conversations", desc: "Create a new, empty conversation." },
      {
        method: "GET",
        path: "/api/conversations/{conversation_id}",
        desc: "Get a conversation and its full message history.",
      },
      {
        method: "PATCH",
        path: "/api/conversations/{conversation_id}",
        desc: "Rename a conversation.",
      },
      {
        method: "DELETE",
        path: "/api/conversations/{conversation_id}",
        desc: "Delete a conversation.",
      },
    ],
  },
  {
    name: "Databases",
    endpoints: [
      {
        method: "POST",
        path: "/api/databases",
        desc: "Register a new external database connection (tested before it's saved).",
      },
      { method: "GET", path: "/api/databases", desc: "List your database connections." },
      {
        method: "DELETE",
        path: "/api/databases/{connection_id}",
        desc: "Delete a database connection.",
      },
      {
        method: "POST",
        path: "/api/databases/{connection_id}/ask",
        desc: "Ask a natural-language question against a connected database (text-to-SQL).",
      },
    ],
  },
];

const METHOD_STYLES = {
  GET: "bg-sky-500/10 text-sky-600 dark:text-sky-400",
  POST: "bg-success/10 text-success",
  PATCH: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  DELETE: "bg-danger/10 text-danger",
};

// Shared pill styling for every inline code/monospace term on this page
// (the intro paragraph's Bearer/Authorization/login route, and each
// endpoint's path below) — bold + the surface-hover pill background so
// these stand out from the surrounding muted body text, not just italic
// monospace at the paragraph's own weight.
const CODE_PILL = "rounded bg-surface-hover px-1.5 py-0.5 font-mono text-sm font-bold text-foreground";

const container = {
  initial: {},
  animate: { transition: { staggerChildren: 0.07 } },
};
const item = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.35, ease: easeOut } },
};

export default function Docs() {
  return (
    <div className="min-h-screen bg-bg">
      <PublicNav active="docs" />

      <main className="mx-auto max-w-3xl px-6 py-16 sm:py-20">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: easeOut }}
          className="text-center"
        >
          <h1 className="mt-2 text-display-xs font-medium leading-tight text-foreground">
            API reference.
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-md text-muted">
            Every route ContextIQ's frontend calls, grouped by resource. All of them require a{" "}
            <code className={CODE_PILL}>Bearer</code> token in the{" "}
            <code className={CODE_PILL}>Authorization</code> header, obtained from{" "}
            <code className={CODE_PILL}>POST /api/auth/login</code>.
          </p>
        </motion.div>

        <motion.div
          initial="initial"
          whileInView="animate"
          viewport={{ once: true, margin: "-40px" }}
          variants={container}
          className="mt-12 flex flex-col gap-10"
        >
          {ENDPOINT_GROUPS.map((group) => (
            <motion.section key={group.name} variants={item}>
              <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-muted">
                {group.name}
              </h2>
              <div className="glass-panel divide-y divide-border overflow-hidden rounded-xl border border-border">
                {group.endpoints.map((ep) => (
                  <div
                    key={`${ep.method} ${ep.path}`}
                    className="flex flex-col gap-2 px-4 py-3.5 sm:flex-row sm:items-center sm:gap-4"
                  >
                    <div className="flex items-center gap-2.5 sm:w-[280px] sm:shrink-0">
                      <span
                        className={`inline-flex w-[52px] shrink-0 justify-center rounded-md px-1.5 py-0.5 text-xs font-medium ${METHOD_STYLES[ep.method]}`}
                      >
                        {ep.method}
                      </span>
                      <code className={`truncate ${CODE_PILL}`}>{ep.path}</code>
                    </div>
                    <p className="text-sm text-muted">{ep.desc}</p>
                  </div>
                ))}
              </div>
            </motion.section>
          ))}
        </motion.div>
      </main>

      <PublicFooter />
    </div>
  );
}
