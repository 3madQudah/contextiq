import { IconMessage2, IconPlugConnected, IconShieldCheck } from "@tabler/icons-react";
import { motion } from "motion/react";

import PublicFooter from "../../components/landing/PublicFooter.jsx";
import PublicNav from "../../components/landing/PublicNav.jsx";
import StepList from "../../components/landing/StepList.jsx";
import { easeOut } from "../../lib/motion.js";

// Copy verified against the actual text-to-SQL pipeline before publishing:
//   1. utils/crypto.py — Fernet symmetric encryption for connection strings
//      at rest; auth/db_connection_models.py — column is literally named
//      encrypted_connection_string, and only ConnectionSummary (id, name,
//      db_type, created_at) ever leaves the API (api/databases_routes.py).
//      test_connection() runs a real connect + SELECT 1 before it's saved.
//   2. chain/sql_chain.py get_schema_snapshot()/format_schema_for_prompt() —
//      introspects the real database via SQLAlchemy's inspector and passes
//      that schema text into the SQL-generation prompt.
//   3. chain/sql_chain.py validate_sql() — single-SELECT + forbidden-keyword
//      check; _readonly_connection() — read-only enforced independently at
//      the connection level per db_type (SQLite URI mode=ro, Postgres
//      session readonly, MySQL SET SESSION TRANSACTION READ ONLY).
// All three checked out — no discrepancies found.
const STEPS = [
  {
    icon: IconPlugConnected,
    title: "Connect your database",
    body: "Add a PostgreSQL, MySQL, or SQLite connection string. Before anything is saved, ContextIQ opens a real connection and runs a test query to confirm it actually works. The connection string is then encrypted at rest (Fernet symmetric encryption) and is never returned by the API afterward — only the connection's name, type, and creation date are.",
  },
  {
    icon: IconMessage2,
    title: "Ask in plain English",
    body: "Your question is sent to the model together with the target database's real schema — table and column names and types, introspected directly from the database itself — so the generated SQL references tables and columns that actually exist, not guesses.",
  },
  {
    icon: IconShieldCheck,
    title: "Two independent safety layers",
    body: "Every generated query is checked against a strict allow-list first: it must be a single SELECT statement, with no stacked statements and none of a long list of forbidden keywords (INSERT, UPDATE, DELETE, DROP, and others). Independently of that check, the database connection itself is opened read-only at the driver level — a read-only file handle for SQLite, a read-only session for PostgreSQL, a read-only transaction for MySQL — so even a query that slipped past validation still couldn't write.",
    note: "Results are also capped (200 rows by default) and every query runs under a statement timeout, so one runaway question can't hang or overwhelm your database.",
  },
];

export default function DatabasesInfo() {
  return (
    <div className="min-h-screen bg-bg">
      <PublicNav active="databases" />

      <main className="mx-auto max-w-3xl px-6 py-16 sm:py-20">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: easeOut }}
          className="text-center"
        >
          <h1 className="mt-2 text-display-xs font-medium leading-tight text-foreground">
            Ask your database questions, safely.
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-md text-muted">
            Connect a live SQL database and ask questions in plain English — ContextIQ writes
            and runs the query for you, with no path to a write it shouldn't make.
          </p>
        </motion.div>

        <div className="mt-12">
          <StepList steps={STEPS} />
        </div>
      </main>

      <PublicFooter />
    </div>
  );
}
