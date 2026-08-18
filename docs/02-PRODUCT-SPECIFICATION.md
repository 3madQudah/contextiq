# 02 — Product Specification

Behavioural specification: the exact rules the code enforces. Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md). Status codes and rules are taken from audit §5, §7, §8.

Related: [01 — Product Requirements](01-PRODUCT-REQUIREMENTS.md) · [06 — API Specification](06-API-SPECIFICATION.md) · [13 — Security](13-SECURITY.md)

---

## 1. Registration & password policy

**Rules enforced** (`auth/schemas.py`, audit §7.5). A password must contain:

| Rule | Constraint |
|---|---|
| Length | ≥ 12 characters (`PASSWORD_MIN_LENGTH = 12`) |
| Uppercase | ≥ 1 `[A-Z]` |
| Lowercase | ≥ 1 `[a-z]` |
| Digit | ≥ 1 `\d` |
| Special | ≥ 1 of `!@#$%^&*()_+-=` |

- **Happy path:** valid body → `201` with `UserResponse` (`id, first_name, last_name, email, created_at`); no password field is returned.
- **Edge cases / errors:**
  - Weak password → `422` (`PydanticCustomError` "password_too_weak", message lists the failed requirements).
  - Invalid email → `422` (Pydantic `EmailStr`).
  - Duplicate email → `400` "Email already registered".
  - More than 5 attempts / 15 min / IP → `429`.
- Enforcement is server-side (source of truth). The frontend mirrors these rules in `PasswordStrengthMeter.jsx` and gates the submit button — defense in depth only (audit §7.5).
- **Acceptance:** a 12+ char password meeting all five classes registers; any missing class is rejected with a message naming it. Covered by `test_auth_security.py` (audit §10).

## 2. Login & tokens

- **Happy path:** correct email + password → `200` `{access_token, token_type:"bearer"}`. Token is a JWT signed `HS256` with claims `sub` (user id) and `exp` (default 60 min) (audit §7.3).
- **Edge cases / errors:**
  - Wrong email or password → `401` "Incorrect email or password" (no field-level disclosure).
  - Invalid body → `422`.
  - More than 5 attempts / 15 min / IP → `429`.
- **Note:** login returns only a token, no user object. The frontend derives `{id: sub, email}` from the JWT + the submitted email (audit §9.3).

## 3. Rate limits (per route)

Library: `slowapi`, keyed by client IP (audit §7.7).

| Route | Limit |
|---|---|
| `POST /api/auth/register` | 5 / 15 minutes / IP |
| `POST /api/auth/login` | 5 / 15 minutes / IP |
| All other routes | none |

- On limit exceed: `429` with `{"detail": "Too many attempts. Please try again later. (limit: …)"}`.
- **Acceptance:** the 6th register or login attempt within the window returns `429` (covered by `test_auth_security.py`).

## 4. Document upload & supported types

**Supported extensions** (`utils/helpers.py`): `.pdf`, `.docx`, `.txt`, `.csv`, `.md`.

- **Happy path:** supported file → saved to `data/raw/{user_id}/{filename}` → loaded → chunked (`chunk_size=1000`, `chunk_overlap=150`) → embedded (`all-MiniLM-L6-v2`) → FAISS index built/updated → chunks appended to `chunks.pkl`. Returns `201` `{filename, chunks_indexed}` (audit §8.1).
- **Edge cases / errors:**
  - Unsupported extension → `400` "Unsupported file type. Allowed: .pdf, .docx, .txt, .csv, .md".
  - Scanned/image PDF (≥ 80% of pages with < 20 non-whitespace chars) → `422` `ScannedPDFError`. The raw file is kept but **not** indexed (audit §8.1).
  - No/invalid token → `401`.
- **Limits / constraints:**
  - No explicit upload size cap is enforced server-side (audit §7.10 — documented gap).
  - Full-document summarize/extract paths cap input at `MAX_DOCUMENT_CHARS = 24_000` chars (see §7).
- **Concurrency:** the frontend serializes uploads one at a time because the per-user FAISS index is rebuilt on each write with no server-side locking (audit §8.1).
- **Acceptance:** a text PDF indexes with `chunks_indexed > 0`; a scanned PDF is rejected with an actionable `422`. Covered by `test_document_loader_pdf.py`.

## 5. Document listing & deletion

- **List:** `GET /api/documents/` → `200` `{documents: sorted filenames}` for the current user's directory (empty list if none).
- **Delete:** `DELETE /api/documents/{file_name}` → removes the raw file, drops its chunks from `chunks.pkl`, and **rebuilds** the FAISS index from all remaining chunks. Returns `200` `{filename, deleted, remaining_chunks}`.
  - Missing file → `404` "Document not found".
  - Cost: rebuild is O(total remaining chunks) — documented scaling caveat (audit §8.1, §14.3).

## 6. Question routing (CSV-compute / full-document / RAG)

For `POST /api/chat/ask`, the handler tries paths in order; the **first non-None result wins** (`chat_routes.py`, audit §4.4, §8):

```
1. CSV computational path   — if file_type == "csv" AND is_computational_question(question)
2. Full-document path       — if file_type in {docx, pdf, md} AND the type's classifier fires
3. RAG path                 — otherwise, or if 1/2 return None (fall back)
```

### 6.1 Classifier gates

| Path | Classifier | Fires on (regex, case-insensitive) |
|---|---|---|
| CSV compute | `csv_query_classifier.is_computational_question` | average/mean/median, total/sum, count/how many/number of, top N, bottom N, highest/largest/max, lowest/smallest/min, group by |
| DOCX full-doc | `docx_query_classifier.is_full_document_question` | word/page count, table of contents / heading list, "what tables"/list tables, list/extract all|every; "summarize" only with a whole/entire/full/overall-document qualifier |
| PDF full-doc | `pdf_query_classifier.is_full_document_question` | same as DOCX plus `outline` |
| MD full-doc | `md_query_classifier.is_full_document_question` | word count, header/heading structure/hierarchy, list/extract all|every; "summarize" only with whole-document qualifier (no page/table patterns) |

A false positive is safe: the compute module returns `None` and the request falls back to RAG (audit §8.3).

### 6.2 CSV computational path (`csv_compute.py`)

- **File resolution:** explicit `file_name` (must be `.csv`), else the sole CSV if exactly one exists; otherwise `None` → fall back to RAG.
- **Loading:** `pd.read_csv(keep_default_na=False, na_values=[""])` so data values like `NA`/`NULL`/`None` are not dropped (only empty cells are missing).
- **Plan building:** operation detected by regex (priority top_n → bottom_n → max → min → mean → median → sum → count). Columns resolved **only** against real DataFrame column names. A single numeric column is auto-selected if none is named. Unresolvable → `None`.
- **Execution:** fixed dispatch over pandas (`sum/mean/median/max/min/count/groupby/sort_values.head`). Operations ∈ `{sum, mean, median, count, max, min, top_n, bottom_n}`. **No `eval`/`exec`/`DataFrame.query`; no user text reaches pandas** (audit §8.3).
- **Phrasing:** the computed fact is handed to the LLM (`temperature=0`) only to phrase; it is instructed not to recompute.
- **Edge cases:** unparseable/empty CSV, ambiguous file (multiple CSVs, no `file_name`), or unresolvable column/operation → fall back to RAG.
- **Acceptance:** average and top-N return exact values; a region literally named `NA` is not silently dropped. Covered by `test_csv_compute.py`.

### 6.3 Full-document path (DOCX / PDF / MD, `*_compute.py`)

- **File resolution:** explicit `file_name` of the right type, else the sole file of that type.
- **Operations** (`ALLOWED_OPERATIONS`):
  - DOCX: `word_count, page_count, heading_list, table_list, summarize, extract_all`.
  - PDF: same six.
  - MD: `word_count, heading_list, summarize, extract_all`.
- **Structural facts computed directly; LLM only phrases them:**
  - **DOCX word count** includes table-cell words. **DOCX page count is refused** (no authoritative value in `.docx`) — word count returned instead.
  - **PDF page count is exact** (read from the page tree). **PDF outline/headings** from `PdfReader.outline` (honestly reports "no outline" when absent). **PDF table extraction is not supported** — honest non-answer, not fabricated data.
  - **MD headings** from section-aware loader.
- **Summarize / extract_all** run the LLM over the **full** document text, capped at `MAX_DOCUMENT_CHARS = 24_000`. Over the cap → explicit refusal (`_too_large_answer`) rather than silent truncation.
- **Scanned PDF** short-circuits to an honest answer.
- **Edge cases:** ambiguous/unreadable file or a question that does not match a full-document pattern → fall back to RAG (`None`).
- **Acceptance:** whole-document summary uses complete text; word/page/heading facts are computed not asked of the LLM; too-large documents are declined. Covered by `test_docx_compute.py`, `test_pdf_compute.py`, `test_md_compute.py`.

### 6.4 RAG path (`rag_chain.py`)

- Rewrite follow-up → standalone query (if history); hybrid retrieve `FETCH_K = 8`; metadata-filter by `file_type`/`file_name`; keep `TOP_K = 4`; assemble context with `[Source: … | Section: …]` headers; select a file-type-tailored prompt if all kept chunks share one type, else the default; answer with `ChatGroq` (`temperature=0`).
- **Edge cases:**
  - User has no index → "You haven't uploaded any documents yet…".
  - Nothing relevant survives filtering → "I couldn't find anything relevant to that question in your documents."
  - Any pipeline exception → `502` "Failed to generate an answer. Please try again." The user's message is kept; no assistant message is fabricated (audit §4.4).

## 7. Conversation lifecycle

- Creating a chat: `POST /api/chat/ask` with `conversation_id: null` creates a conversation titled from the first question; the frontend then renames it via a client-side heuristic (`lib/titles.js`).
- Ownership: every `/{conversation_id}` route and `/chat/ask` uses `get_owned_conversation_by_id`. A missing OR foreign id both return `404` — indistinguishable, no existence leak (audit §7.6).
- Rename requires a non-empty `title` (`422` otherwise). Delete returns `204`; cascades to messages (audit §6.1).

## 8. Text-to-SQL constraints

**Connection creation** (`POST /api/databases`): the server performs a real connect + `SELECT 1` before saving; failure → `400` "Could not connect to the database: …". The connection string is stored **encrypted** (Fernet) and never returned by any response (audit §7.8, §7.9).

**Query** (`POST /api/databases/{id}/ask`) enforces, in order (audit §7.9, §8.5):

1. **Text validation** (`validate_sql`): strip comments; must start with `SELECT`; reject stacked queries (`;` + more); reject a forbidden-keyword set (`INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, REVOKE, EXEC, EXECUTE, ATTACH, DETACH, PRAGMA, CREATE, REPLACE, MERGE, CALL, VACUUM, REINDEX, COPY, OUTFILE, DUMPFILE, LOAD_FILE`). Failure → `400` "Generated query was rejected ({layer}): …".
2. **Read-only connection:** sqlite `mode=ro` URI; Postgres `postgresql_readonly=True`; MySQL `SET SESSION TRANSACTION READ ONLY`.
3. **Statement timeout** (10s default): Postgres `statement_timeout`; MySQL `MAX_EXECUTION_TIME`; sqlite progress-handler abort. **MariaDB does not honor `MAX_EXECUTION_TIME`** — documented gap (audit §7.9).
4. **Row cap** (200 default): fetches `row_limit + 1` to detect truncation; the displayed SQL always shows `LIMIT {row_limit}`.

- **Error states:** `400` validation; `504` `SQLExecutionTimeout` (our timeout fired); `503` `SQLConnectionError` (connection lost/refused; MySQL errnos `2003/2006/2013/4031` + message markers); `502` any unclassified failure; `404` connection not owned.
- **Acceptance:** timeout vs connection-lost vs passthrough classification is unit-tested (`test_sql_chain.py`, 20 cases). The validator is regex-level, not a full SQL parser — the read-only connection is the real write guard (audit §7.10, [09 — Decisions](09-DECISIONS.md)).

## 9. Per-user isolation guarantees

From audit §7.6:

| Surface | Enforcement |
|---|---|
| Retrieval | Separate FAISS + BM25 indexes per `user_id` on disk; a different index is loaded per user. |
| Documents | Keyed by `data/raw/{current_user.id}/` — list/upload/delete only within the user's own directory. |
| Conversations | `get_owned_conversation_by_id` — missing/foreign → `404`. |
| DB connections | `get_owned_connection_by_id` — missing/foreign → `404`. |

`metadata_filter.py` only narrows results **within** a user's own documents; it is not the isolation boundary (the per-user index is).

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [My Portfolio](https://emadqudah.vercel.app/index.html) · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
