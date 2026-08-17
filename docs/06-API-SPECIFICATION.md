# 06 — API Specification

Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §5.

All routes are mounted with the prefixes from `main.py`. "Auth: JWT" means the `get_current_user` dependency (HTTP Bearer). Error bodies are `{"detail": ...}`. In examples, `$TOKEN` is a placeholder for a real access token and `localhost:8000` is the default backend origin.

Related: [02 — Product Specification](02-PRODUCT-SPECIFICATION.md) · [05 — Data Model](05-DATA-MODEL.md)

---

## 1. Endpoint summary

| Method + Path | Handler (file) | Auth | Rate limit | Success |
|---|---|---|---|---|
| `GET /health` | `health_check` (`main.py`) | Public | none | 200 |
| `POST /api/auth/register` | `register` (`auth_routes.py`) | Public | 5/15min/IP | 201 |
| `POST /api/auth/login` | `login` (`auth_routes.py`) | Public | 5/15min/IP | 200 |
| `POST /api/documents/upload` | `upload_document` (`documents_routes.py`) | JWT | none | 201 |
| `GET /api/documents/` | `list_documents` | JWT | none | 200 |
| `DELETE /api/documents/{file_name}` | `delete_document` | JWT | none | 200 |
| `POST /api/chat/ask` | `ask` (`chat_routes.py`) | JWT | none | 200 |
| `GET /api/conversations` | `list_conversations` | JWT | none | 200 |
| `POST /api/conversations` | `create_conversation` | JWT | none | 201 |
| `GET /api/conversations/{conversation_id}` | `get_conversation` | JWT (+owner) | none | 200 |
| `PATCH /api/conversations/{conversation_id}` | `rename_conversation` | JWT (+owner) | none | 200 |
| `DELETE /api/conversations/{conversation_id}` | `delete_conversation` | JWT (+owner) | none | 204 |
| `POST /api/databases` | `create_connection` (`databases_routes.py`) | JWT | none | 201 |
| `GET /api/databases` | `list_connections` | JWT | none | 200 |
| `DELETE /api/databases/{connection_id}` | `delete_connection` | JWT (+owner) | none | 204 |
| `POST /api/databases/{connection_id}/ask` | `ask_database` | JWT (+owner) | none | 200 |

---

## 2. Endpoint detail

### `GET /health`

Public. Returns `200 {"status": "ok"}`.

```bash
curl http://localhost:8000/health
```

### `POST /api/auth/register`

- Auth: public. Rate limit: 5/15min/IP.
- Body `RegisterRequest`: `first_name: str` (req), `last_name: str` (req), `email: EmailStr` (req), `password: str` (req, strength-validated — see [02 §1](02-PRODUCT-SPECIFICATION.md)).
- Success `201` `UserResponse`: `{id, first_name, last_name, email, created_at}` (no password field).
- Errors: `422` weak password (`password_too_weak`) or invalid email; `400` "Email already registered"; `429` rate limit.

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com","password":"Str0ng!Passw0rd"}'
```

### `POST /api/auth/login`

- Auth: public. Rate limit: 5/15min/IP.
- Body `LoginRequest`: `email: EmailStr`, `password: str`.
- Success `200` `TokenResponse`: `{access_token, token_type:"bearer"}`.
- Errors: `401` "Incorrect email or password"; `422` invalid body; `429` rate limit.

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ada@example.com","password":"Str0ng!Passw0rd"}'
```

### `POST /api/documents/upload`

- Auth: JWT.
- Body: `multipart/form-data`, field `file`.
- Behavior: rejects unsupported extensions; saves to `data/raw/{user_id}/`; loads → chunks → embeds → indexes.
- Success `201` `{filename, chunks_indexed}`.
- Errors: `400` "Unsupported file type. Allowed: .pdf, .docx, .txt, .csv, .md"; `422` `ScannedPDFError` (scanned/image PDF); `401` no/invalid token.

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@./report.pdf"
```

### `GET /api/documents/`

- Auth: JWT. Success `200` `{documents: [filenames]}` (empty list if none).
- Errors: `401`.

```bash
curl http://localhost:8000/api/documents/ -H "Authorization: Bearer $TOKEN"
```

### `DELETE /api/documents/{file_name}`

- Auth: JWT. `file_name` is the identifier (no document-id table).
- Behavior: removes the raw file, drops its chunks, rebuilds the FAISS index.
- Success `200` `{filename, deleted, remaining_chunks}`.
- Errors: `404` "Document not found"; `401`.

```bash
curl -X DELETE "http://localhost:8000/api/documents/report.pdf" \
  -H "Authorization: Bearer $TOKEN"
```

### `POST /api/chat/ask`

- Auth: JWT.
- Body `ChatRequest`: `question: str` (req), `conversation_id: int|null`, `file_type: str|null`, `file_name: str|null`.
- Behavior: routes to CSV-compute / full-document / RAG (see [02 §6](02-PRODUCT-SPECIFICATION.md)); persists the exchange.
- Success `200` `ChatResponse`: `{answer, sources: [str], conversation_id, rewritten_query: str|null}`.
- Errors: `404` conversation not owned/found (when `conversation_id` given); `502` "Failed to generate an answer. Please try again." (any pipeline exception); `401`.

```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"question":"Summarize the whole document","conversation_id":null,"file_type":"pdf","file_name":"report.pdf"}'
```

### `GET /api/conversations`

- Auth: JWT. Success `200` `[ConversationSummary]` (`id, title, created_at, updated_at, message_count`), ordered by `updated_at` desc.
- Errors: `401`.

```bash
curl http://localhost:8000/api/conversations -H "Authorization: Bearer $TOKEN"
```

### `POST /api/conversations`

- Auth: JWT. Body `ConversationCreateRequest`: `title: str|null` (defaults to "New conversation").
- Success `201` `ConversationSummary`.
- Errors: `401`.

```bash
curl -X POST http://localhost:8000/api/conversations \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Q3 analysis"}'
```

### `GET /api/conversations/{conversation_id}`

- Auth: JWT + ownership. Success `200` `ConversationDetail` (summary + `messages: [{id, role, content, sources?, created_at}]`).
- Errors: `404` not owned/found; `401`.

```bash
curl http://localhost:8000/api/conversations/42 -H "Authorization: Bearer $TOKEN"
```

### `PATCH /api/conversations/{conversation_id}`

- Auth: JWT + ownership. Body `ConversationRenameRequest`: `title: str` (req).
- Success `200` `ConversationSummary`.
- Errors: `404`; `422` missing title; `401`.

```bash
curl -X PATCH http://localhost:8000/api/conversations/42 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Renamed"}'
```

### `DELETE /api/conversations/{conversation_id}`

- Auth: JWT + ownership. Success `204` (no body). Cascades to messages.
- Errors: `404`; `401`.

```bash
curl -X DELETE http://localhost:8000/api/conversations/42 -H "Authorization: Bearer $TOKEN"
```

### `POST /api/databases`

- Auth: JWT. Body `ConnectionCreateRequest`: `name: str`, `db_type: "postgresql"|"mysql"|"sqlite"`, `connection_string: str`.
- Behavior: performs a real connect + `SELECT 1` before saving; stores the string encrypted (Fernet).
- Success `201` `ConnectionSummary`: `{id, name, db_type, created_at}`.
- Errors: `400` "Could not connect to the database: …" / malformed / db_type mismatch; `422` invalid `db_type`; `401`.

```bash
curl -X POST http://localhost:8000/api/databases \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Analytics","db_type":"postgresql","connection_string":"postgresql://user:pass@host:5432/db"}'
```

### `GET /api/databases`

- Auth: JWT. Success `200` `[ConnectionSummary]`, ordered by `created_at` desc. `encrypted_connection_string` is never returned.
- Errors: `401`.

```bash
curl http://localhost:8000/api/databases -H "Authorization: Bearer $TOKEN"
```

### `DELETE /api/databases/{connection_id}`

- Auth: JWT + ownership. Success `204`.
- Errors: `404` not owned/found; `401`.

```bash
curl -X DELETE http://localhost:8000/api/databases/7 -H "Authorization: Bearer $TOKEN"
```

### `POST /api/databases/{connection_id}/ask`

- Auth: JWT + ownership. Body `DBQueryRequest`: `question: str`.
- Behavior: introspect schema → generate SQL → validate → execute read-only with timeout → summarize (see [04 §6](04-ARCHITECTURE.md)).
- Success `200` `DBQueryResponse`: `{answer, sql_query, columns: [str], rows: [[...]], row_count, truncated}`.
- Errors: `400` `SQLValidationError` "Generated query was rejected ({layer}): …"; `504` `SQLExecutionTimeout`; `503` `SQLConnectionError`; `502` any unclassified failure; `404` not owned; `401`.

```bash
curl -X POST http://localhost:8000/api/databases/7/ask \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"question":"How many rows are in each table?"}'
```

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
