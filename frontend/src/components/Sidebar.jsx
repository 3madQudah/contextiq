import { Database, Files, LogOut, Pencil, Plus, Trash2 } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { NavLink, useMatch, useNavigate } from "react-router-dom";

import { useAppData } from "../context/AppDataContext.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { deleteConversation, renameConversation } from "../services/api.js";
import { getDisplayName, getInitials } from "../lib/user.js";
import ConfirmDialog from "./ConfirmDialog.jsx";
import Logo from "./Logo.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

export default function Sidebar({ onNavigate = () => {} }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  // Not useParams(): Sidebar is a sibling of <Outlet/> inside AppLayout, not
  // rendered through it, so it sits outside the RouteContext that carries
  // chat/:conversationId's params — useParams() here would always be
  // undefined. useMatch reads the actual URL instead, which works regardless
  // of where in the tree it's called.
  const match = useMatch("/app/chat/:conversationId");
  const activeId = match?.params?.conversationId;
  const {
    conversations,
    conversationsLoading,
    conversationsError,
    refreshConversations,
    documents,
    databaseConnections,
  } = useAppData();

  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  function startRename(conversation) {
    setEditingId(conversation.id);
    setEditValue(conversation.title);
  }

  async function commitRename(conversation) {
    const title = editValue.trim();
    setEditingId(null);
    if (!title || title === conversation.title) return;
    try {
      await renameConversation(conversation.id, title);
      refreshConversations();
    } catch {
      refreshConversations(); // revert any optimistic UI by re-syncing with the server
    }
  }

  async function confirmDelete() {
    setDeleting(true);
    try {
      await deleteConversation(deleteTarget.id);
      await refreshConversations();
      if (String(deleteTarget.id) === activeId) {
        navigate("/app/chat");
      }
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  }

  function handleNewChat() {
    onNavigate();
    navigate("/app/chat");
  }

  return (
    <div className="flex h-full flex-col bg-surface">
      <div className="flex items-center px-4 pb-3 pt-4">
        <Logo size="sm" />
      </div>

      <div className="px-3">
        {/* Fixed (non-theme-adaptive) white/black outline — same "Get
            started" treatment used on the public site, not the shared
            Button component's `invert` variant, since that variant's base
            classes hardcode font-medium and this needs bold text. */}
        <motion.button
          type="button"
          onClick={handleNewChat}
          whileHover={{ scale: 1.015 }}
          whileTap={{ scale: 0.96 }}
          transition={{ type: "spring", stiffness: 420, damping: 30 }}
          className="flex w-full items-center justify-center gap-2 rounded-md border-[1.5px] border-black bg-white px-3 py-2 text-sm font-bold text-black transition-colors hover:bg-zinc-50"
        >
          <Plus size={16} strokeWidth={2} />
          New chat
        </motion.button>
      </div>

      <div className="mt-4 flex-1 overflow-y-auto px-3">
        <p className="px-1 pb-1.5 text-xs text-muted">Conversations</p>

        {conversationsLoading && (
          <p className="px-1 py-2 text-sm text-muted">Loading…</p>
        )}
        {conversationsError && (
          <p className="px-1 py-2 text-sm text-danger">{conversationsError}</p>
        )}
        {!conversationsLoading && !conversationsError && conversations.length === 0 && (
          <p className="px-1 py-2 text-sm text-muted">No conversations yet.</p>
        )}

        <ul className="flex flex-col gap-0.5">
          {conversations.map((conversation) => {
            const isActive = String(conversation.id) === activeId;
            const isEditing = editingId === conversation.id;

            return (
              <li key={conversation.id} className="group relative">
                {isEditing ? (
                  <input
                    autoFocus
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={() => commitRename(conversation)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") e.currentTarget.blur();
                      if (e.key === "Escape") setEditingId(null);
                    }}
                    className="w-full rounded-md border border-accent/40 bg-surface px-2 py-1.5 text-sm text-foreground focus-visible:ring-2 focus-visible:ring-accent/40"
                  />
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      onNavigate();
                      navigate(`/app/chat/${conversation.id}`);
                    }}
                    className={`flex w-full items-center rounded-md px-2 py-1.5 text-left text-sm transition-colors ${
                      isActive
                        ? "bg-accent/10 text-accent"
                        : "text-foreground hover:bg-surface-hover"
                    }`}
                  >
                    <span className="flex-1 truncate pr-12">{conversation.title}</span>
                  </button>
                )}

                {!isEditing && (
                  <div className="absolute inset-y-0 right-1 flex items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
                    <button
                      type="button"
                      aria-label="Rename conversation"
                      onClick={() => startRename(conversation)}
                      className="flex h-6 w-6 items-center justify-center rounded text-muted hover:bg-surface-hover hover:text-foreground"
                    >
                      <Pencil size={13} strokeWidth={1.5} />
                    </button>
                    <button
                      type="button"
                      aria-label="Delete conversation"
                      onClick={() => setDeleteTarget(conversation)}
                      className="flex h-6 w-6 items-center justify-center rounded text-muted hover:bg-surface-hover hover:text-danger"
                    >
                      <Trash2 size={13} strokeWidth={1.5} />
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </div>

      <div className="border-t border-border px-3 py-3">
        <NavLink
          to="/app/documents"
          onClick={onNavigate}
          className={({ isActive }) =>
            `flex items-center justify-between rounded-md px-2 py-1.5 text-sm transition-colors ${
              isActive ? "bg-accent/10 text-accent" : "text-foreground hover:bg-surface-hover"
            }`
          }
        >
          <span className="flex items-center gap-2">
            <Files size={16} strokeWidth={1.5} />
            Documents
          </span>
          <span className="text-xs text-muted">{documents.length}</span>
        </NavLink>

        <NavLink
          to="/app/databases"
          onClick={onNavigate}
          className={({ isActive }) =>
            `mt-0.5 flex items-center justify-between rounded-md px-2 py-1.5 text-sm transition-colors ${
              isActive ? "bg-accent/10 text-accent" : "text-foreground hover:bg-surface-hover"
            }`
          }
        >
          <span className="flex items-center gap-2">
            <Database size={16} strokeWidth={1.5} />
            Databases
          </span>
          <span className="text-xs text-muted">{databaseConnections.length}</span>
        </NavLink>
      </div>

      <div className="flex items-center gap-2 border-t border-border px-3 py-3">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-black text-xs font-medium text-white">
          {getInitials(user)}
        </div>
        <span className="flex-1 truncate text-sm text-foreground">{getDisplayName(user)}</span>
        <ThemeToggle />
        <button
          type="button"
          aria-label="Log out"
          title="Log out"
          onClick={logout}
          className="flex h-8 w-8 items-center justify-center rounded-md text-muted hover:bg-surface-hover hover:text-foreground"
        >
          <LogOut size={16} strokeWidth={1.5} />
        </button>
      </div>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete conversation?"
        description={
          deleteTarget ? `"${deleteTarget.title}" and all its messages will be deleted.` : ""
        }
        confirmLabel="Delete"
        loading={deleting}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={confirmDelete}
      />
    </div>
  );
}
