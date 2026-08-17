# 01 — Product Requirements

Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md). Every capability below maps to a real endpoint (audit §5) or frontend route (audit §9.1).

Related: [02 — Product Specification](02-PRODUCT-SPECIFICATION.md) · [06 — API Specification](06-API-SPECIFICATION.md)

---

## 1. Problem statement

People accumulate documents (PDFs, Word files, spreadsheets, notes, Markdown) and structured data in SQL databases, and need answers from them without reading everything or writing SQL. Two recurring failure modes of naive retrieval-augmented generation motivate this project:

1. **Pure vector search misses exact tokens.** Semantic embeddings are weak at exact IDs, codes, and numbers. ContextIQ's own evaluation shows BM25-only or vector-only each miss questions the hybrid retriever recovers (audit §11).
2. **Top-K retrieval silently answers structural/aggregate questions from a partial sample.** "What is the average of column X", "how many pages", "list every date" cannot be answered reliably from a handful of retrieved chunks. ContextIQ computes or reads the complete source for those cases instead of guessing (audit §8.3, §8.4).

## 2. Who it is for

- Individuals who want to ask questions across their own uploaded documents with answers cited back to the source file.
- Users who want to query an external SQL database in plain English without writing SQL, over a read-only connection.

Each account is isolated: documents, conversations, and search indexes never cross between users (audit §7.6).

## 3. Goals

| # | Goal | Evidence in code |
|---|---|---|
| G1 | Ground every answer in the user's own documents and cite the source file. | `run_rag_chain` returns `sources`; `BASE_INSTRUCTIONS` requires citation (audit §8.2, §8.7). |
| G2 | Hybrid retrieval so exact terms and numbers are found. | `EnsembleRetriever([FAISS, BM25], weights=[0.5, 0.5])` (audit §8.2). |
| G3 | Answer aggregate/structural questions exactly, not from a sample. | CSV compute + DOCX/PDF/MD full-document paths (audit §8.3, §8.4). |
| G4 | Query external SQL databases in natural language, safely (read-only). | `sql_chain` with regex validation + read-only connection (audit §7.9, §8.5). |
| G5 | Per-user isolation of all data and indexes. | Per-user FAISS/BM25 dirs; ownership dependencies (audit §7.6). |
| G6 | Fail honestly rather than fabricate. | Scanned-PDF rejection, too-large refusals, "couldn't find anything relevant", `502` on LLM failure without a fabricated assistant message (audit §4.4, §8.1, §8.4). |

## 4. Non-goals (as built)

Derived from audit §14.2. These are explicitly **not** implemented:

- **OCR** for scanned/image PDFs — rejected at upload with an actionable error instead.
- **PDF table extraction** — returns an honest non-answer.
- **DOCX page count** — deliberately not reported (no authoritative value); word count returned instead.
- **Persisted database-query history** — the ask-a-database view is session-only.
- **LLM-generated conversation titles** — a client-side heuristic is used.
- **Server-side token revocation / refresh tokens.**
- **Deployment to a hosting provider** — Planned, not implemented (audit §14.4).

## 5. User-facing capabilities (as built)

Every capability corresponds to a real route (audit §9.1) and endpoint (audit §5.1).

| Capability | Frontend route | Backend endpoint(s) |
|---|---|---|
| Register an account | `/register` | `POST /api/auth/register` |
| Log in | `/login` | `POST /api/auth/login` |
| Upload a document | `/app/documents` | `POST /api/documents/upload` |
| List / delete documents | `/app/documents` | `GET /api/documents/`, `DELETE /api/documents/{file_name}` |
| Ask questions about documents (cited) | `/app/chat`, `/app/chat/:conversationId` | `POST /api/chat/ask` |
| Manage conversations | sidebar (`/app`) | `GET/POST /api/conversations`, `GET/PATCH/DELETE /api/conversations/{id}` |
| Register / list / delete an external DB connection | `/app/databases` | `POST/GET /api/databases`, `DELETE /api/databases/{id}` |
| Ask a database in plain English | `/app/databases/:connectionId` | `POST /api/databases/{id}/ask` |
| Public marketing/docs pages | `/`, `/product`, `/databases`, `/docs` | — (static content) |
| Service health | — | `GET /health` |

## 6. User stories mapped to endpoints

| As a user I want to… | So that… | Endpoint |
|---|---|---|
| create an account with a strong password | my data is private to me | `POST /api/auth/register` |
| log in and stay signed in across restarts | I don't re-auth constantly | `POST /api/auth/login` (token in `localStorage`, audit §9.3) |
| upload a PDF/DOCX/CSV/TXT/MD | I can ask questions about it | `POST /api/documents/upload` |
| get a cited answer to a question | I can verify it against the source | `POST /api/chat/ask` → `answer` + `sources` |
| filter the next question to one file type | I scope the search | `POST /api/chat/ask` with `file_type`/`file_name` |
| ask "average of column X" and get an exact number | aggregates aren't estimated from a sample | `POST /api/chat/ask` (`file_type="csv"`, computational path, audit §8.3) |
| ask "summarize the whole document" | I get the full document, not the first chunks | `POST /api/chat/ask` (full-document path, audit §8.4) |
| rename or delete a conversation | I keep my history tidy | `PATCH`/`DELETE /api/conversations/{id}` |
| connect a Postgres/MySQL/SQLite database | I can query it without SQL | `POST /api/databases` (tested with a real connect) |
| ask the database a question and see the SQL | I trust and can audit the query | `POST /api/databases/{id}/ask` → `answer`, `sql_query`, `columns`, `rows` |

## 7. Success criteria

| Criterion | Measure | Current status |
|---|---|---|
| Hybrid retrieval recovers exact-value questions single retrievers miss | Recall@4 on the eval set | Met on the synthetic corpus: BM25-only 89.3% vs Hybrid 100.0% (audit §11) |
| Answers are cited | `sources` present on document answers | Met (audit §8.2) |
| Aggregates are exact | CSV compute over full file | Met, unit-tested (audit §10) |
| Text-to-SQL never writes | Regex validation + read-only connection | Met, error classification unit-tested (audit §7.9, §10) |
| Per-user isolation | Ownership checks + per-user indexes | Met by construction (audit §7.6) |
| Backend test suite green | `pytest backend/tests/` | 58 passing (audit §10) |

> The evaluation corpus is a synthetic 10-document / ~17-chunk fixture. Results illustrate hybrid-vs-single-retriever behavior, **not** production-scale performance. See [03 — Technical Specification](03-TECHNICAL-SPECIFICATION.md) and audit §11 before citing numbers.

## 8. Out of scope (this version)

From audit §14.2. Not started or intentionally excluded: OCR, PDF table extraction, DOCX page count, persisted DB query history, LLM conversation titles, persisted `rewritten_query`, and any hosted deployment (Planned — not implemented, audit §14.4).

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
