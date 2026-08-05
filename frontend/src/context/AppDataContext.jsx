import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { getErrorMessage, listConversations, listDatabaseConnections, listDocuments } from "../services/api.js";

// Shared across the app shell so the sidebar's conversation list and
// document count stay in sync no matter which page (Chat, Documents)
// triggered the change — one fetch, one source of truth, instead of each
// page/component re-fetching and drifting out of sync with the others.
const AppDataContext = createContext(null);

export function AppDataProvider({ children }) {
  const [conversations, setConversations] = useState([]);
  const [conversationsLoading, setConversationsLoading] = useState(true);
  const [conversationsError, setConversationsError] = useState("");

  const [documents, setDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState("");

  const [databaseConnections, setDatabaseConnections] = useState([]);
  const [databaseConnectionsLoading, setDatabaseConnectionsLoading] = useState(true);
  const [databaseConnectionsError, setDatabaseConnectionsError] = useState("");

  const refreshConversations = useCallback(async () => {
    setConversationsLoading(true);
    setConversationsError("");
    try {
      const data = await listConversations();
      setConversations(data);
    } catch (err) {
      setConversationsError(getErrorMessage(err, "Couldn't load conversations."));
    } finally {
      setConversationsLoading(false);
    }
  }, []);

  const refreshDocuments = useCallback(async () => {
    setDocumentsLoading(true);
    setDocumentsError("");
    try {
      const data = await listDocuments();
      setDocuments(data.documents ?? []);
    } catch (err) {
      setDocumentsError(getErrorMessage(err, "Couldn't load documents."));
    } finally {
      setDocumentsLoading(false);
    }
  }, []);

  const refreshDatabaseConnections = useCallback(async () => {
    setDatabaseConnectionsLoading(true);
    setDatabaseConnectionsError("");
    try {
      const data = await listDatabaseConnections();
      setDatabaseConnections(data);
    } catch (err) {
      setDatabaseConnectionsError(getErrorMessage(err, "Couldn't load database connections."));
    } finally {
      setDatabaseConnectionsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshConversations();
    refreshDocuments();
    refreshDatabaseConnections();
  }, [refreshConversations, refreshDocuments, refreshDatabaseConnections]);

  const value = useMemo(
    () => ({
      conversations,
      conversationsLoading,
      conversationsError,
      refreshConversations,
      documents,
      documentsLoading,
      documentsError,
      refreshDocuments,
      databaseConnections,
      databaseConnectionsLoading,
      databaseConnectionsError,
      refreshDatabaseConnections,
    }),
    [
      conversations,
      conversationsLoading,
      conversationsError,
      refreshConversations,
      documents,
      documentsLoading,
      documentsError,
      refreshDocuments,
      databaseConnections,
      databaseConnectionsLoading,
      databaseConnectionsError,
      refreshDatabaseConnections,
    ]
  );

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>;
}

export function useAppData() {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error("useAppData must be used within AppDataProvider");
  return ctx;
}
