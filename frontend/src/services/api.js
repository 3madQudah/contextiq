import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const TOKEN_KEY = "contextiq.token";

// localStorage (not sessionStorage): this is a personal document-search tool
// a user expects to stay logged into across browser restarts, not a
// per-tab banking session — see AuthContext.jsx for the full note.
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url = error.config?.url || "";
    // A 401 from /auth/login is just "wrong password" — not a stale session.
    // Only treat 401s from *other* (bearer-protected) calls as "log the user
    // out", since that's what actually means the token is gone/expired.
    const isAuthEndpoint = url.includes("/api/auth/login") || url.includes("/api/auth/register");
    if (status === 401 && !isAuthEndpoint) {
      clearToken();
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// FastAPI error bodies are either {detail: "string"} (our own HTTPExceptions)
// or {detail: [{loc, msg, type}, ...]} (automatic Pydantic 422s). Normalize
// both into one display string.
export function getErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const detail = error?.response?.data?.detail;
  if (!detail) return error?.message || fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(", ");
  }
  return fallback;
}

export async function registerUser({ first_name, last_name, email, password }) {
  const { data } = await api.post("/api/auth/register", { first_name, last_name, email, password });
  return data;
}

export async function loginUser({ email, password }) {
  const { data } = await api.post("/api/auth/login", { email, password });
  return data;
}

export async function listDocuments() {
  const { data } = await api.get("/api/documents/");
  return data;
}

export async function uploadDocument(file, onUploadProgress) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/api/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });
  return data;
}

export async function deleteDocument(fileName) {
  const { data } = await api.delete(`/api/documents/${encodeURIComponent(fileName)}`);
  return data;
}

export async function listConversations() {
  const { data } = await api.get("/api/conversations");
  return data;
}

export async function createConversation(title) {
  // The backend marks this request body required even though every field on
  // it is optional — omitting the body entirely 422s, so always send an object.
  const { data } = await api.post("/api/conversations", { title: title ?? null });
  return data;
}

export async function getConversation(conversationId) {
  const { data } = await api.get(`/api/conversations/${conversationId}`);
  return data;
}

export async function renameConversation(conversationId, title) {
  const { data } = await api.patch(`/api/conversations/${conversationId}`, { title });
  return data;
}

export async function deleteConversation(conversationId) {
  await api.delete(`/api/conversations/${conversationId}`);
}

export async function askQuestion({ question, conversation_id, file_type, file_name }) {
  const { data } = await api.post("/api/chat/ask", {
    question,
    conversation_id: conversation_id ?? null,
    file_type: file_type ?? null,
    file_name: file_name ?? null,
  });
  return data;
}

export async function listDatabaseConnections() {
  const { data } = await api.get("/api/databases");
  return data;
}

export async function createDatabaseConnection({ name, db_type, connection_string }) {
  const { data } = await api.post("/api/databases", { name, db_type, connection_string });
  return data;
}

export async function deleteDatabaseConnection(connectionId) {
  await api.delete(`/api/databases/${connectionId}`);
}

export async function askDatabaseQuestion(connectionId, question) {
  const { data } = await api.post(`/api/databases/${connectionId}/ask`, { question });
  return data;
}

export async function checkHealth() {
  const { data } = await api.get("/health");
  return data;
}

export default api;
