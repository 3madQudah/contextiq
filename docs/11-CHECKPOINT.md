# 11 — Checkpoint

Snapshot date: **2026-08-18**. Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §10, §12, §14.

Related: [07 — Implementation Plan](07-IMPLEMENTATION-PLAN.md) · [08 — Roadmap](08-ROADMAP.md)

---

## Git status

- Branch: `main`, up to date with `origin/main`.
- Working tree: **clean** — this checkpoint update (alongside the README live-demo links) is the pending commit.
- Committed history: five commits — `afa0d94` (2026-08-05, "first commit"), `f4d5b34` (2026-08-08, hybrid eval / per-type prompts / compute paths / docs), `9a66a45` (security hardening, Docker stack, landing pages, full docs), `6de41d6` (CPU-only torch build for the Render free-tier memory limit), `b820eec` (Render + Vercel config, dynamic PORT, demo banner, deployment docs).

## Test status

- `pytest backend/tests/` → **58 passed** (re-verified 2026-08-18, ~19.8s, under Python 3.13.9). Zero failures/skips.

## Deployment status

Live and verified, not just documented:

- Backend live on Render (free tier), Postgres attached, CPU-only torch build to fit the 512MB memory limit (idle usage measured at ~417MB before deploy).
- Frontend live on Vercel, wired to the Render backend via `VITE_API_BASE_URL`.
- `FRONTEND_ORIGIN` on Render updated to the real Vercel origin — CORS confirmed working.
- End-to-end smoke test passed: registered a real account, uploaded a real PDF, asked a real question, got a real answer with citations.
- Demo banner live on the deployed frontend, matching the design system.

Known accepted limitations of this free-tier deployment:

- Ephemeral filesystem — uploads and their FAISS indexes are wiped on every redeploy.
- Free Postgres instance expires 30 days after creation.
- Cold start after 15 minutes of inactivity (~30–60s to wake).

Live URLs: see the README's [Live Demo](../README.md#live-demo) section.

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
- Persistent-disk / no-cold-start hosting — current deployment is Render free tier (see Deployment status above); moving to a paid plan or external object storage is a next action below.

## What is blocked and why

| Blocked | Blocking reason |
|---|---|
| Managed-DB schema evolution | No Alembic; `create_all` cannot alter existing tables (§6.3). |
| CI gating | No CI configured (§14.4). |

## Known data artifacts

- Orphaned `backend/data/vector_index/3/` with no matching `data/raw/3/` (audit §1.5).
- `contextiq.db` present at both repo root and `backend/` (both gitignored); which is used depends on process cwd.

## Exact next three actions

1. **Set a calendar reminder** to recreate the Postgres instance before it expires (~30 days from 2026-08-18) and update `DATABASE_URL` on Render.
2. **Decide** whether to move to Render Starter ($7/mo) for persistent disk + no cold starts, or migrate uploads/indexes to S3 (per [08 — Roadmap](08-ROADMAP.md)).
3. **Add the live demo link** to CV / LinkedIn / GitHub profile README.

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
