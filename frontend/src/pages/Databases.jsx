import { AlertCircle, Database as DatabaseIcon, Info, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Button from "../components/Button.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import EmptyState from "../components/EmptyState.jsx";
import PasswordInput from "../components/PasswordInput.jsx";
import Select from "../components/Select.jsx";
import TextInput from "../components/TextInput.jsx";
import { useAppData } from "../context/AppDataContext.jsx";
import { getDbTypeLabel } from "../lib/databaseTypes.js";
import { createDatabaseConnection, deleteDatabaseConnection, getErrorMessage } from "../services/api.js";

const EMPTY_FORM = { name: "", db_type: "postgresql", connection_string: "" };

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export default function Databases() {
  const navigate = useNavigate();
  const {
    databaseConnections,
    databaseConnectionsLoading,
    databaseConnectionsError,
    refreshDatabaseConnections,
  } = useAppData();

  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [testing, setTesting] = useState(false);
  const [formError, setFormError] = useState("");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  function openForm() {
    setForm(EMPTY_FORM);
    setFormError("");
    setFormOpen(true);
  }

  function closeForm() {
    setFormOpen(false);
    setFormError("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.name.trim() || !form.connection_string.trim()) {
      setFormError("Name and connection string are required.");
      return;
    }
    setFormError("");
    setTesting(true);
    try {
      await createDatabaseConnection(form);
      await refreshDatabaseConnections();
      setFormOpen(false);
      setForm(EMPTY_FORM);
    } catch (err) {
      // A 400 here means the backend actually attempted to connect and it
      // failed (bad host, auth, unreachable, ...) — surface that message
      // verbatim rather than a generic fallback, so the user knows what to fix.
      setFormError(getErrorMessage(err, "Couldn't save this connection."));
    } finally {
      setTesting(false);
    }
  }

  async function confirmDelete() {
    setDeleting(true);
    try {
      await deleteDatabaseConnection(deleteTarget.id);
      await refreshDatabaseConnections();
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  }

  return (
    <div className="mx-auto h-full max-w-2xl overflow-y-auto px-6 py-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-lg font-medium text-foreground">Databases</h1>
          <p className="mt-1 text-sm text-muted">
            Connect an external SQL database and ask questions about it in plain language.
          </p>
        </div>
        {!formOpen && (
          <Button variant="primary" onClick={openForm} className="shrink-0">
            <Plus size={15} strokeWidth={1.5} />
            Add connection
          </Button>
        )}
      </div>

      {formOpen && (
        <form
          onSubmit={handleSubmit}
          className="mt-6 flex flex-col gap-4 rounded-lg border border-border bg-surface p-5"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-base font-medium text-foreground">Add connection</h2>
            <button
              type="button"
              aria-label="Cancel"
              onClick={closeForm}
              className="text-muted hover:text-foreground"
            >
              <X size={16} strokeWidth={1.5} />
            </button>
          </div>

          <TextInput
            label="Name"
            name="name"
            placeholder="e.g. Production analytics"
            required
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />

          <Select
            label="Database type"
            name="db_type"
            value={form.db_type}
            onChange={(e) => setForm((f) => ({ ...f, db_type: e.target.value }))}
          >
            <option value="postgresql">PostgreSQL</option>
            <option value="mysql">MySQL</option>
            <option value="sqlite">SQLite</option>
          </Select>

          <PasswordInput
            label="Connection string"
            name="connection_string"
            placeholder="postgresql://user:password@host:5432/dbname"
            autoComplete="off"
            required
            value={form.connection_string}
            onChange={(e) => setForm((f) => ({ ...f, connection_string: e.target.value }))}
          />

          <div className="flex items-start gap-2 rounded-md border border-border bg-surface-hover px-3 py-2.5 text-sm text-muted">
            <Info size={15} strokeWidth={1.5} className="mt-0.5 shrink-0" />
            <span>
              Use a read-only database user if your database supports one. This app blocks write queries
              before they run, but it can&apos;t fully guarantee that at the database permission level — a
              dedicated read-only account is the strongest protection against accidental data changes.
            </span>
          </div>

          {formError && (
            <div className="flex items-start gap-2 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
              <AlertCircle size={15} strokeWidth={1.5} className="mt-0.5 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={closeForm} disabled={testing}>
              Cancel
            </Button>
            <Button type="submit" loading={testing}>
              {testing ? "Testing connection…" : "Test & save"}
            </Button>
          </div>
        </form>
      )}

      <div className="mt-8">
        {databaseConnectionsLoading && <p className="text-sm text-muted">Loading connections…</p>}

        {databaseConnectionsError && <p className="text-sm text-danger">{databaseConnectionsError}</p>}

        {!databaseConnectionsLoading &&
          !databaseConnectionsError &&
          databaseConnections.length === 0 &&
          !formOpen && (
            <EmptyState
              icon={DatabaseIcon}
              title="No databases connected"
              body="Connect an external SQL database to ask questions about it in plain language — no SQL required."
              action={
                <Button variant="primary" onClick={openForm}>
                  Add your first connection
                </Button>
              }
            />
          )}

        {!databaseConnectionsLoading && !databaseConnectionsError && databaseConnections.length > 0 && (
          <ul className="flex flex-col gap-2">
            {databaseConnections.map((conn) => (
              <li key={conn.id} className="group relative">
                <button
                  type="button"
                  onClick={() => navigate(`/app/databases/${conn.id}`)}
                  className="flex w-full items-center gap-3 rounded-md border border-border px-3.5 py-3 pr-10 text-left transition-colors hover:bg-surface-hover"
                >
                  <DatabaseIcon size={16} strokeWidth={1.5} className="shrink-0 text-muted" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm text-foreground">{conn.name}</span>
                      <span className="shrink-0 rounded-full border border-border px-2 py-0.5 text-xs text-muted">
                        {getDbTypeLabel(conn.db_type)}
                      </span>
                    </div>
                    <p className="mt-0.5 text-sm text-muted">Added {formatDate(conn.created_at)}</p>
                  </div>
                </button>
                <button
                  type="button"
                  aria-label={`Delete ${conn.name}`}
                  onClick={() => setDeleteTarget(conn)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted opacity-0 transition-opacity hover:text-danger group-hover:opacity-100"
                >
                  <Trash2 size={15} strokeWidth={1.5} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete connection?"
        description={
          deleteTarget
            ? `"${deleteTarget.name}" will be removed. You can always reconnect it later.`
            : ""
        }
        confirmLabel="Delete"
        loading={deleting}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={confirmDelete}
      />
    </div>
  );
}
