# 09 — Decisions (ADRs)

Architecture Decision Records for decisions evidenced in the code. Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md). Each records what was gained **and** what was given up.

Related: [04 — Architecture](04-ARCHITECTURE.md) · [08 — Roadmap](08-ROADMAP.md) · [13 — Security](13-SECURITY.md)

---

## ADR-001 — Hybrid FAISS + BM25 retrieval, weights 0.5/0.5

- **Status:** Accepted.
- **Context:** Pure vector search underperforms on exact IDs, codes, and numbers. The eval (§11) shows BM25-only misses three exact-value questions (q04, q14, q15) that hybrid recovers (+12.0% recall vs BM25-only).
- **Decision:** Combine FAISS (semantic) and BM25 (keyword) via LangChain `EnsembleRetriever` with equal weights `[0.5, 0.5]` (`chain/hybrid_retriever.py`), pulling 8 per retriever, fetching 8, keeping top 4.
- **Consequences:**
  - Gained: exact-term recall without losing semantic recall.
  - Given up: higher per-query latency than a single retriever (p50 ~12.4ms hybrid vs ~0.7ms BM25-only in the eval), and both indexes are rebuilt per call with no caching.
  - The 0.5/0.5 weighting was tested against 0.6/0.4, 0.7/0.3, 0.8/0.2 (`weight_tuning_summary.md`): Precision/Recall identical; MRR/MAP move only +0.006 from a single question re-ranking. **No generalizable gain from re-weighting on a 17-chunk corpus**, so the default stays 0.5/0.5.

## ADR-002 — Per-user FAISS/BM25 index instead of one shared index with metadata filtering

- **Status:** Accepted.
- **Context:** Retrieval must never cross between users.
- **Decision:** Each user gets their own on-disk index directory (`data/vector_index/{user_id}/`) and `chunks.pkl`; a different index is loaded per user (`ingestion/vector_store.py`, `keyword_store.py`). `metadata_filter.py` only narrows results *within* a user's own documents.
- **Consequences:**
  - Gained: isolation is structural — a query can only see the loading user's index, not a filter that could be forgotten or bypassed.
  - Given up: no cross-user index reuse; each delete rebuilds that user's whole index (O(remaining chunks)); indexes are rebuilt on every retrieval call. Scaling past hundreds of documents per user would want FAISS delete-by-id and caching (§14.3, [08 — Roadmap](08-ROADMAP.md) L1/L2).

## ADR-003 — Dedicated compute paths with regex classifier gates instead of RAG-for-everything

- **Status:** Accepted.
- **Context:** Top-K retrieval cannot reliably answer aggregate/structural/exhaustive questions from a partial chunk sample (a CSV average, a page count, "list every date").
- **Decision:** Route CSV computational questions to exact pandas aggregation (`csv_compute.py`) and DOCX/PDF/MD structural/exhaustive questions to full-document paths (`*_compute.py`), gated by cheap regex classifiers (`*_query_classifier.py`). Compute-first, LLM-phrases-only; fall back to RAG (`None`) whenever a plan can't be confidently built.
- **Consequences:**
  - Gained: exact aggregates and structural facts instead of estimates; explicit refusals over the 24k-char cap instead of silent truncation.
  - Given up: regex classifiers are permissive and can false-positive (safe — they fall back to RAG) or false-negative (question goes through RAG as before); more code paths to maintain per file type.

## ADR-004 — Read-only text-to-SQL with defense-in-depth (regex validator + read-only connection)

- **Status:** Accepted.
- **Context:** LLM-generated SQL run against a user's real database must never write.
- **Decision:** Two independent layers (`chain/sql_chain.py`): (1) text-level `validate_sql` — must start with `SELECT`, no stacked queries, forbidden-keyword blocklist; (2) a genuinely read-only connection per DB type (sqlite `mode=ro`, Postgres `postgresql_readonly=True`, MySQL `SET SESSION TRANSACTION READ ONLY`) plus a statement timeout and row cap.
- **Consequences:**
  - Gained: even if validation is bypassed, the connection itself rejects writes at the DB/session level.
  - Given up / honest limitation: **the validator is regex-level, not a real SQL parser** — a keyword or `;` hidden inside a string literal could evade the text checks (documented in the code). This is exactly why the read-only connection is the real write guard, not the regex. MariaDB does not honor `MAX_EXECUTION_TIME`, so its statement timeout is not server-enforced (§7.9).

## ADR-005 — JWT stored in `localStorage`

- **Status:** Accepted (with a known trade-off).
- **Context:** The app is a personal document tool expected to stay logged in across browser restarts.
- **Decision:** Store the access token (and a minimal user object) in `localStorage` (`services/api.js`, `AuthContext.jsx`); attach it as a Bearer header via an axios interceptor.
- **Consequences:**
  - Gained: persistent sessions across restarts; simple client implementation; no cookie/CSRF plumbing.
  - Given up: `localStorage` is readable by any injected script — **an XSS vuln would expose the token**. There is also no server-side revocation; a token is valid until `exp` (default 60 min). Mitigations/alternatives tracked in [08 — Roadmap](08-ROADMAP.md) L3/L4 and [13 — Security](13-SECURITY.md).

## ADR-006 — Schema via `create_all` instead of Alembic migrations

- **Status:** Accepted (acknowledged debt).
- **Context:** Early-stage project; fast iteration on models.
- **Decision:** Create tables at startup with `Base.metadata.create_all(bind=engine)` (`main.py`); no migration framework.
- **Consequences:**
  - Gained: zero migration ceremony during development; a fresh DB just works.
  - Given up: `create_all` only creates **missing** tables — it does not alter existing ones. Any schema change on a populated database is unmanaged. This is explicit technical debt; introducing Alembic is a near-term roadmap item ([08 — Roadmap](08-ROADMAP.md) N3).

## ADR-007 — Fernet encryption of external DB connection strings at rest

- **Status:** Accepted.
- **Context:** The text-to-SQL feature stores user database credentials; these must not be readable from the app DB and must never leave the API.
- **Decision:** Encrypt connection strings with Fernet (AES-128-CBC + HMAC, `cryptography`) using `DB_ENCRYPTION_KEY` (`utils/crypto.py`); store only the ciphertext (`encrypted_connection_string`); exclude it from every response schema (`ConnectionSummary` returns `id, name, db_type, created_at` only).
- **Consequences:**
  - Gained: credentials are not stored in plaintext and are never returned by the API.
  - Given up: `DB_ENCRYPTION_KEY` becomes a critical, non-rotatable-in-place secret — rotating it renders existing ciphertexts undecryptable (`decrypt` raises on `InvalidToken`); if unset, the feature raises at use time. Key management is a hard dependency.

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
