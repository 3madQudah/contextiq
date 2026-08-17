# 07 — Implementation Plan

Reconstructed from the code and the two commits in [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §12. Phase status is marked honestly against what exists in the repo.

Related: [08 — Roadmap](08-ROADMAP.md) · [11 — Checkpoint](11-CHECKPOINT.md) · [14 — Deployment](14-DEPLOYMENT.md)

---

## Commit history (ground truth)

| Hash | Date | Subject |
|---|---|---|
| `afa0d94` | 2026-08-05 | first commit |
| `f4d5b34` | 2026-08-08 | Add hybrid retrieval evaluation, per-file-type prompts, computational query paths, and project documentation |

The working tree currently has 27 modified + 21 untracked files that are **not yet committed** (audit §12), including the Docker stack, rate limiter, security/SQL tests, and marketing/landing frontend. Those are captured as "In progress" below and in [10 — Changelog](10-CHANGELOG.md) (Unreleased).

---

## Phase 1 — Foundation & auth — **Done**

Evidence: `auth/` package, `api/auth_routes.py`, `api/dependencies.py`, `auth/database.py`, `test_auth.py`.

- [x] FastAPI app skeleton, CORS, `/health`.
- [x] SQLAlchemy engine/session; SQLite default with Postgres/MySQL support and `postgres://` normalization.
- [x] `User` model; register/login; JWT issuance and the `get_current_user` dependency.
- [x] Password hashing (passlib/bcrypt).
- [x] Auth tests (register, duplicate email, login, wrong password).

## Phase 2 — Document ingestion & RAG — **Done**

Evidence: `loaders/document_loader.py`, `ingestion/*`, `chain/rag_chain.py`, `chain/hybrid_retriever.py`, `api/documents_routes.py`, `api/chat_routes.py`.

- [x] Per-type loaders; section-aware DOCX/MD; scanned-PDF detection.
- [x] Chunking (1000/150) with metadata tagging.
- [x] Embeddings (`all-MiniLM-L6-v2`), per-user FAISS + BM25 indexes.
- [x] Hybrid `EnsembleRetriever` (0.5/0.5), `FETCH_K=8`, `TOP_K=4`.
- [x] Query rewriting from conversation history; metadata filtering; cited answers.
- [x] Upload/list/delete endpoints; chat endpoint; conversations CRUD.

## Phase 3 — Conversations & history — **Done**

Evidence: `auth/chat_models.py`, `api/conversations_routes.py`.

- [x] `Conversation`/`Message` models with cascade delete.
- [x] List/create/get/rename/delete conversations with ownership enforcement.
- [x] Recent-history injection (3 turn-pairs) into rewrite + answering prompts.

## Phase 4 — Text-to-SQL — **Done**

Evidence: `chain/sql_chain.py`, `api/databases_routes.py`, `auth/db_connection_models.py`, `utils/crypto.py`.

- [x] Encrypted connection storage (Fernet); connection test on create.
- [x] Schema introspection (cached 60s) → SQL generation (Groq).
- [x] Regex validation (SELECT-only, forbidden keywords) + read-only connection + statement timeout + row cap.
- [x] `OperationalError` classification → `503`/`504`/`502`.

## Phase 5 — Per-file-type prompts & compute paths — **Done** (commit `f4d5b34`)

Evidence: `prompt_eng/*`, `chain/{csv,docx,pdf,md}_compute.py`, `chain/*_query_classifier.py`, compute tests.

- [x] `PROMPT_REGISTRY` with per-type templates + default fallback.
- [x] CSV computational path (exact pandas aggregation, safe dispatch).
- [x] Full-document paths for DOCX/PDF/MD (structural facts + summarize/extract with 24k char cap).
- [x] Regex classifier gates routing questions to compute vs RAG.

## Phase 6 — Retrieval evaluation — **Done** (commit `f4d5b34`)

Evidence: `eval/` (harness, fixtures, results, weight sweep).

- [x] FAISS-only / BM25-only / Hybrid harness over a labeled 28-question set.
- [x] Precision/Recall/MRR/MAP + latency; category breakdown.
- [x] Weight sweep; recommendation to keep 0.5/0.5.

## Phase 7 — Security hardening & UI polish — **In progress** (uncommitted working tree)

Evidence (untracked/modified, audit §12): `utils/rate_limit.py`, `test_auth_security.py`, `test_sql_chain.py`, marketing pages, landing components, toast/aurora/pipeline components, `lib/motion.js`, Docker files.

- [x] Password strength policy + rate limiting (with tests) — code present, **not committed**.
- [x] MySQL error-classification tests — present, not committed.
- [x] Marketing/landing frontend, toasts, theme, animation tokens — present, not committed.
- [ ] Commit the working tree (currently dirty).

## Phase 8 — Deployment — **Not started**

README states "Planned (Render + Vercel), instructions coming soon" (audit §14.4). A Docker Compose stack exists, but no hosting configuration, migrations, CI, or secret management is in place. Ordered, checkable tasks:

1. [ ] **Rotate the leaked secrets** committed in `.env.example` (`SECRET_KEY`, `DB_ENCRYPTION_KEY`, `GROQ_API_KEY`) and replace with placeholders. (First, blocking.)
2. [ ] Introduce Alembic; generate an initial migration matching the current schema; switch startup off `create_all` for managed environments.
3. [ ] Provision managed Postgres; set `DATABASE_URL` (verify `postgres://` normalization path).
4. [ ] Provision a persistent volume for `backend/data/` (FAISS indexes, `chunks.pkl`, raw uploads); confirm the container `DATABASE_URL` points inside it.
5. [ ] Set the production env-var checklist: `SECRET_KEY`, `DB_ENCRYPTION_KEY`, `GROQ_API_KEY`, `DATABASE_URL`, `FRONTEND_ORIGIN`.
6. [ ] Set `FRONTEND_ORIGIN` to the deployed frontend origin (CORS is single-origin).
7. [ ] Build the frontend with the correct `VITE_API_BASE_URL` (compiled in at build time; must be browser-reachable).
8. [ ] Deploy backend (container) and frontend (static/nginx); verify `/health` and `/healthz`.
9. [ ] Add CI (lint + `pytest backend/tests/`) — none exists today.
10. [ ] Add an upload size cap and filename sanitization before exposing uploads publicly (see [13 — Security](13-SECURITY.md)).

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
