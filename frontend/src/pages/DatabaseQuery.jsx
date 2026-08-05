import { ArrowLeft, Database as DatabaseIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import Composer from "../components/Composer.jsx";
import DatabaseAnswer from "../components/DatabaseAnswer.jsx";
import TypingIndicator from "../components/TypingIndicator.jsx";
import { useAppData } from "../context/AppDataContext.jsx";
import { getDbTypeLabel } from "../lib/databaseTypes.js";
import { askDatabaseQuestion, getErrorMessage } from "../services/api.js";

// Fully generic on purpose — this page has no access to the target
// database's schema client-side, so examples can't reference real table
// names the way Chat's document examples can reference "my documents".
const EXAMPLE_QUESTIONS = [
  "How many rows are in each table?",
  "What tables are available in this database?",
];

export default function DatabaseQuery() {
  const { connectionId } = useParams();
  const { databaseConnections, databaseConnectionsLoading } = useAppData();
  const connection = databaseConnections.find((c) => String(c.id) === connectionId);

  // Session-only: there's no backend support for persisting DB query
  // history (unlike document chat's conversations), so this resets on
  // reload or when switching connections.
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    setMessages([]);
  }, [connectionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  async function handleSend(question) {
    const userMessage = { id: `local-user-${Date.now()}`, role: "user", question };
    setMessages((prev) => [...prev, userMessage]);
    setSending(true);

    try {
      const data = await askDatabaseQuestion(connectionId, question);
      setMessages((prev) => [
        ...prev,
        { id: `local-assistant-${Date.now()}`, role: "assistant", result: data },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `local-error-${Date.now()}`,
          role: "assistant",
          error: true,
          content: getErrorMessage(err, "Failed to answer the question against this database."),
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  if (!connection) {
    return (
      <div className="mx-auto flex h-full max-w-2xl flex-col items-center justify-center gap-2 px-6 text-center">
        {databaseConnectionsLoading ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : (
          <>
            <p className="text-sm text-muted">This connection couldn&apos;t be found.</p>
            <Link to="/app/databases" className="text-sm text-accent hover:underline">
              Back to Databases
            </Link>
          </>
        )}
      </div>
    );
  }

  const showEmptyState = messages.length === 0 && !sending;

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-border px-4 py-3 sm:px-8">
        <Link
          to="/app/databases"
          aria-label="Back to Databases"
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-muted hover:bg-surface-hover hover:text-foreground"
        >
          <ArrowLeft size={16} strokeWidth={1.5} />
        </Link>
        <DatabaseIcon size={15} strokeWidth={1.5} className="shrink-0 text-muted" />
        <span className="truncate text-sm font-medium text-foreground">{connection.name}</span>
        <span className="shrink-0 rounded-full border border-border px-2 py-0.5 text-xs text-muted">
          {getDbTypeLabel(connection.db_type)}
        </span>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">
        <div className="mx-auto flex max-w-2xl flex-col gap-5">
          {showEmptyState && (
            <div className="flex flex-col items-center gap-4 py-16 text-center">
              <DatabaseIcon size={22} strokeWidth={1.5} className="text-muted" />
              <div>
                <h2 className="text-base font-medium text-foreground">Ask this database a question</h2>
                <p className="mt-1 text-sm text-muted">
                  Every answer shows the exact read-only SQL query that was run.
                </p>
              </div>
              <div className="flex flex-col gap-2">
                {EXAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="rounded-md border border-border px-3.5 py-2 text-sm text-foreground transition-colors hover:bg-surface-hover"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) =>
            message.role === "user" ? (
              <div key={message.id} className="flex justify-end">
                <div className="max-w-[75%] rounded-lg bg-surface-hover px-3.5 py-2 text-base text-foreground">
                  {message.question}
                </div>
              </div>
            ) : message.error ? (
              <p key={message.id} className="text-base text-danger">
                {message.content}
              </p>
            ) : (
              <DatabaseAnswer key={message.id} result={message.result} />
            )
          )}

          {sending && <TypingIndicator />}
        </div>
      </div>

      <Composer onSend={handleSend} disabled={sending} placeholder="Ask a question about this database…" />
    </div>
  );
}
