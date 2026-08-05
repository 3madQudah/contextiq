import { AlertCircle, FileSearch, Loader2, Trash2, X } from "lucide-react";
import { useRef, useState } from "react";

import Button from "../components/Button.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import Dropzone from "../components/Dropzone.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { useAppData } from "../context/AppDataContext.jsx";
import { ACCEPTED_EXTENSIONS, getFileIcon, isAcceptedFile } from "../lib/fileTypes.js";
import { deleteDocument, getErrorMessage, uploadDocument } from "../services/api.js";

const FIRST_UPLOAD_DONE_KEY = "contextiq.hasUploadedBefore";

export default function Documents() {
  const { documents, documentsLoading, documentsError, refreshDocuments } = useAppData();
  const inputRef = useRef(null);
  const chainRef = useRef(Promise.resolve());

  const [uploads, setUploads] = useState([]);
  const [rejectionMessage, setRejectionMessage] = useState("");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  function handleFilesSelected(files) {
    const accepted = [];
    const rejected = [];
    for (const file of files) {
      (isAcceptedFile(file.name) ? accepted : rejected).push(file);
    }

    setRejectionMessage(
      rejected.length
        ? `${rejected.map((f) => f.name).join(", ")} — unsupported file type. Allowed: ${ACCEPTED_EXTENSIONS.join(", ")}`
        : ""
    );

    accepted.forEach(queueUpload);
  }

  function queueUpload(file) {
    const key = `${file.name}-${Date.now()}-${Math.random()}`;
    setUploads((prev) => [
      ...prev,
      { key, name: file.name, progress: 0, phase: "queued", error: "" },
    ]);
    // Uploads are processed one at a time (not in parallel): the backend
    // rebuilds a single per-user FAISS index file on each write with no
    // locking, so concurrent uploads for the same user could race and
    // corrupt it. Queuing client-side avoids relying on the backend for that.
    chainRef.current = chainRef.current.then(() => processUpload(key, file));
  }

  async function processUpload(key, file) {
    const isFirstEver = !localStorage.getItem(FIRST_UPLOAD_DONE_KEY);
    setUploads((prev) =>
      prev.map((u) => (u.key === key ? { ...u, phase: "uploading" } : u))
    );
    try {
      await uploadDocument(file, (evt) => {
        const progress = evt.total ? Math.round((evt.loaded / evt.total) * 100) : 0;
        setUploads((prev) =>
          prev.map((u) =>
            u.key === key
              ? { ...u, progress, phase: progress >= 100 ? "embedding" : "uploading", isFirstEver }
              : u
          )
        );
      });
      localStorage.setItem(FIRST_UPLOAD_DONE_KEY, "1");
      setUploads((prev) => prev.map((u) => (u.key === key ? { ...u, phase: "done" } : u)));
      await refreshDocuments();
      setTimeout(() => {
        setUploads((prev) => prev.filter((u) => u.key !== key));
      }, 2000);
    } catch (err) {
      setUploads((prev) =>
        prev.map((u) =>
          u.key === key ? { ...u, phase: "error", error: getErrorMessage(err, "Upload failed.") } : u
        )
      );
    }
  }

  function dismissUpload(key) {
    setUploads((prev) => prev.filter((u) => u.key !== key));
  }

  async function confirmDeleteDocument() {
    setDeleting(true);
    try {
      await deleteDocument(deleteTarget);
      await refreshDocuments();
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  }

  return (
    <div className="mx-auto h-full max-w-2xl overflow-y-auto px-6 py-8">
      <h1 className="text-lg font-medium text-foreground">Documents</h1>
      <p className="mt-1 text-sm text-muted">
        Upload files here so you can ask questions about them in chat.
      </p>

      <div className="mt-6">
        <Dropzone inputRef={inputRef} onFiles={handleFilesSelected} />
      </div>

      {rejectionMessage && (
        <div className="mt-3 flex items-start gap-2 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          <AlertCircle size={15} strokeWidth={1.5} className="mt-0.5 shrink-0" />
          <span className="flex-1">{rejectionMessage}</span>
          <button onClick={() => setRejectionMessage("")} aria-label="Dismiss">
            <X size={14} strokeWidth={1.5} />
          </button>
        </div>
      )}

      {uploads.length > 0 && (
        <div className="mt-4 flex flex-col gap-2">
          {uploads.map((u) => (
            <div key={u.key} className="rounded-md border border-border px-3 py-2.5">
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-sm text-foreground">{u.name}</span>
                {u.phase === "error" ? (
                  <button onClick={() => dismissUpload(u.key)} aria-label="Dismiss">
                    <X size={14} strokeWidth={1.5} className="text-muted" />
                  </button>
                ) : u.phase === "done" ? (
                  <span className="text-xs text-muted">Indexed</span>
                ) : null}
              </div>

              {u.phase === "uploading" && (
                <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-surface-hover">
                  <div
                    className="h-full rounded-full bg-accent transition-all duration-200"
                    style={{ width: `${u.progress}%` }}
                  />
                </div>
              )}

              {u.phase === "embedding" && (
                <div className="mt-1.5 flex items-center gap-1.5 text-sm text-muted">
                  <Loader2 size={13} strokeWidth={1.5} className="animate-spin" />
                  <span>
                    Generating embeddings…
                    {u.isFirstEver && " first run downloads the model, this can take a minute."}
                  </span>
                </div>
              )}

              {u.phase === "error" && (
                <p className="mt-1.5 text-sm text-danger">{u.error}</p>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-8">
        {documentsLoading && <p className="text-sm text-muted">Loading documents…</p>}

        {documentsError && (
          <p className="text-sm text-danger">{documentsError}</p>
        )}

        {!documentsLoading && !documentsError && documents.length === 0 && (
          <EmptyState
            icon={FileSearch}
            title="Nothing indexed yet"
            body="Upload a PDF, spreadsheet, or notes file above to start asking questions about it in chat."
            action={
              <Button variant="primary" onClick={() => inputRef.current?.click()}>
                Upload a document
              </Button>
            }
          />
        )}

        {!documentsLoading && !documentsError && documents.length > 0 && (
          <ul className="flex flex-col gap-1">
            {documents.map((name) => {
              const Icon = getFileIcon(name);
              return (
                <li
                  key={name}
                  className="group flex items-center gap-3 rounded-md border border-border px-3 py-2.5"
                >
                  <Icon size={16} strokeWidth={1.5} className="shrink-0 text-muted" />
                  <span className="flex-1 truncate text-sm text-foreground">{name}</span>
                  <button
                    type="button"
                    aria-label={`Delete ${name}`}
                    onClick={() => setDeleteTarget(name)}
                    className="text-muted opacity-0 transition-opacity hover:text-danger group-hover:opacity-100"
                  >
                    <Trash2 size={15} strokeWidth={1.5} />
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete document?"
        description={
          deleteTarget
            ? `"${deleteTarget}" will be removed and its content will no longer be searchable.`
            : ""
        }
        confirmLabel="Delete"
        loading={deleting}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={confirmDeleteDocument}
      />
    </div>
  );
}
