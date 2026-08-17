# 10 — Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/). Reconstructed from the two real commits in [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §12. **No release dates or version tags exist in the repo** — commit dates are shown where known; version numbers below are editorial placeholders, not git tags.

---

## [Unreleased]

Uncommitted working-tree changes (27 modified + 21 untracked files, audit §12). Not yet committed.

### Added
- Auth rate limiting via slowapi (`utils/rate_limit.py`): 5/15min/IP on register and login, with a `429` handler.
- Password-strength validation tests (`tests/test_auth_security.py`) and MySQL error-classification tests for text-to-SQL (`tests/test_sql_chain.py`).
- Docker stack: `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `docker-compose.yml`, `.dockerignore` files.
- Marketing/landing frontend: `pages/marketing/*`, `components/landing/*`, `PipelineDiagram`, `AuroraBackground`, `PasswordStrengthMeter`, toast system (`ToastContext`, `ToastViewport`), shared animation tokens (`lib/motion.js`).

### Changed
- Modified across auth routes, databases routes, `sql_chain.py`, `main.py`, several frontend pages/components, and `requirements.txt` (per the working-tree diff, audit §12).

### Security
- **Outstanding:** `.env.example` contains real-looking committed secrets (`SECRET_KEY`, `DB_ENCRYPTION_KEY`, `GROQ_API_KEY`) that must be rotated and replaced with placeholders — see [13 — Security](13-SECURITY.md).

---

## [0.2.0] — 2026-08-08

Commit `f4d5b34`: "Add hybrid retrieval evaluation, per-file-type prompts, computational query paths, and project documentation."

### Added
- Per-file-type prompt templates and `PROMPT_REGISTRY` (`prompt_eng/*`) with a default fallback.
- CSV computational path: exact pandas aggregation over the full file with a safe fixed-dispatch executor (`chain/csv_compute.py`, `csv_query_classifier.py`).
- Full-document paths for DOCX/PDF/MD: structural facts (word/page count, headings, tables) and whole-document summarize/extract with a 24k-char cap and explicit refusals (`chain/{docx,pdf,md}_compute.py` + classifiers).
- Retrieval evaluation harness (`eval/`): FAISS-only vs BM25-only vs Hybrid over a 28-question labeled set; Precision/Recall/MRR/MAP + latency; weight sweep and recommendation to keep 0.5/0.5.
- Project documentation (`README.md`, `PROJECT_TREE.md`).

---

## [0.1.0] — 2026-08-05

Commit `afa0d94`: "first commit".

### Added
- FastAPI application skeleton, CORS, `/health`.
- Auth: `User` model, register/login, JWT, `get_current_user`, password hashing.
- Document ingestion: per-type loaders, scanned-PDF detection, section-aware DOCX/MD, chunking, embeddings, per-user FAISS + BM25 indexes.
- RAG pipeline: hybrid retrieval, query rewriting from history, metadata filtering, cited answers.
- Conversations: `Conversation`/`Message` models and CRUD with ownership enforcement.
- Text-to-SQL: encrypted connections, schema introspection, SQL generation, regex validation, read-only execution with timeout and row cap.
- React SPA: auth, chat, documents, databases views; theming; shared API client.
- Backend tests: auth, CSV/DOCX/PDF/MD compute paths, scanned-PDF detection.

> Note: the two commits above bracket the currently-committed history. Some features listed under 0.1.0 vs 0.2.0 are attributed by the commit that added the corresponding files per audit §12; exact per-file commit attribution beyond the two commits is not recoverable from the repo.

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
