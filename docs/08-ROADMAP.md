# 08 — Roadmap

Ordered by priority, not dated. Near-term items are the real gaps in [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §14.2–§14.4. Nothing here is implemented unless it also appears as Done in [07 — Implementation Plan](07-IMPLEMENTATION-PLAN.md).

Related: [09 — Decisions](09-DECISIONS.md) · [13 — Security](13-SECURITY.md) · [14 — Deployment](14-DEPLOYMENT.md)

---

## Near-term (correctness, security, ship)

| # | Item | Why | Source |
|---|---|---|---|
| N1 | Rotate leaked secrets in `.env.example`; replace with placeholders | Real-looking `SECRET_KEY`/`DB_ENCRYPTION_KEY`/`GROQ_API_KEY` are committed | §7.10, §14.3 |
| N2 | Remove insecure `SECRET_KEY` fallback default | Falls back to a known literal if env unset | §7.10 |
| N3 | Add Alembic migrations | Schema is `create_all`-only; cannot evolve a populated DB | §6.3, §14.4 |
| N4 | Implement deployment (Render + Vercel/static) | Currently "Planned — not implemented" | §14.4 |
| N5 | Add CI (lint + `pytest backend/tests/`) | No CI exists | §14.4 |
| N6 | Enforce an upload size cap on `/api/documents/upload` | No size limit today | §7.10 |
| N7 | Sanitize `file.filename` before path join | Unsanitized filename used in raw path | §7.10 |
| N8 | Commit the dirty working tree | 27 modified + 21 untracked files uncommitted | §12 |

## Mid-term (capability gaps)

| # | Item | Current behavior | Source |
|---|---|---|---|
| M1 | OCR for scanned/image PDFs | Rejected at upload with an actionable `422` | §14.2 |
| M2 | PDF table extraction | Honest non-answer (pypdf can't; needs pdfplumber/camelot) | §14.2 |
| M3 | LLM-generated conversation titles | Client-side heuristic (`lib/titles.js`) | §14.2 |
| M4 | Persisted database-query history | Ask-a-database view is session-only | §14.2 |
| M5 | Larger, non-synthetic eval corpus | Current corpus is 17 chunks / 10 docs (synthetic) | §11, §14.2 |
| M6 | Persist `rewritten_query` on messages | Only shown for live/session messages | §14.2 |
| M7 | MariaDB statement-timeout support | `MAX_EXECUTION_TIME` silently ignored on MariaDB | §7.9 |

## Long-term (defensible extensions)

These follow directly from the existing architecture; each is a natural extension, not a new product.

| # | Item | Rationale |
|---|---|---|
| L1 | FAISS delete-by-id instead of full rebuild on delete | Document delete is currently O(remaining chunks); an id-mapping alongside `chunks.pkl` would make it O(deleted) (§14.3, code note in `vector_store.py`). |
| L2 | Per-user index caching / concurrency control | Indexes are rebuilt on every retrieval call and every write with no locking (§14.3). |
| L3 | Token refresh + server-side revocation | JWT is valid until `exp`; no logout-server-side (§7.10). |
| L4 | Move token storage off `localStorage` (e.g. httpOnly cookie) | Reduce XSS exposure of the token (§7.10). |
| L5 | Multi-origin CORS support | Single `FRONTEND_ORIGIN` today (§14.3). |
| L6 | Answer-quality evaluation (not just retrieval) | Current eval measures retrieval only (§11). |

Cross-references: security items map to [13 — Security §Known limitations](13-SECURITY.md); deployment items to [14 — Deployment](14-DEPLOYMENT.md).

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
