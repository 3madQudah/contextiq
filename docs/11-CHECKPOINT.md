# 11 — Checkpoint

Snapshot date: **2026-08-17**. Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §10, §12, §14.

Related: [07 — Implementation Plan](07-IMPLEMENTATION-PLAN.md) · [08 — Roadmap](08-ROADMAP.md)

---

## Git status

- Branch: `main`.
- Working tree: **not clean** — 27 modified tracked files + 21 untracked new paths, uncommitted (audit §12).
- Committed history: two commits — `afa0d94` (2026-08-05, "first commit"), `f4d5b34` (2026-08-08, hybrid eval / per-type prompts / compute paths / docs).

## Test status

- `pytest backend/tests/` → **58 passed** (verified this session, ~17s, under Python 3.13.9). Zero failures/skips (audit §10).

## What works (verified)

From audit §14.1:

- Auth: register (strength-validated), login (JWT), rate limiting, password hashing — covered by passing tests.
- Per-file-type compute paths: CSV aggregation; DOCX/PDF/MD structural + summarize/extract with size cap and honest refusals; scanned-PDF detection — covered by passing tests.
- Text-to-SQL error classification (timeout vs connection-lost vs passthrough) — covered by passing tests.
- RAG pipeline, hybrid retrieval, ingestion, ownership isolation, and the conversations/documents/databases routes — present and internally consistent (not directly unit-tested; see [12 — Testing](12-TESTING.md)).
- Docker build/run stack and the eval harness with recorded results.

## What is incomplete

From audit §14.2:

- OCR — not implemented (scanned PDFs rejected at upload).
- PDF table extraction — honest non-answer.
- DOCX page count — deliberately refused (word count returned).
- Persisted DB query history — session-only.
- LLM conversation titles — client-side heuristic.
- `rewritten_query` — not persisted.
- MariaDB statement timeout — silently ignored.
- Deployment — Planned, not implemented (audit §14.4).

## What is blocked and why

| Blocked | Blocking reason |
|---|---|
| Public deployment | Leaked committed secrets must be rotated first (audit §7.10, §14.3); no migrations or hosting config exist (§14.4). |
| Managed-DB schema evolution | No Alembic; `create_all` cannot alter existing tables (§6.3). |
| CI gating | No CI configured (§14.4). |

## Known data artifacts

- Orphaned `backend/data/vector_index/3/` with no matching `data/raw/3/` (audit §1.5).
- `contextiq.db` present at both repo root and `backend/` (both gitignored); which is used depends on process cwd.

## Exact next three actions

1. **Rotate** the leaked `SECRET_KEY`, `DB_ENCRYPTION_KEY`, and `GROQ_API_KEY` values and replace `.env.example` entries with placeholders; remove the insecure `SECRET_KEY` fallback default.
2. **Commit** the working tree (rate limiter, security/SQL tests, Docker stack, marketing frontend) so the tree is clean and the changelog Unreleased section can be cut.
3. **Introduce Alembic** and generate an initial migration matching the current schema, ahead of any managed-Postgres deployment.

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
