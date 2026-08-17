# 12 — Testing

Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §10.

Related: [07 — Implementation Plan](07-IMPLEMENTATION-PLAN.md) · [15 — Contributing](15-CONTRIBUTING.md)

---

## 1. Framework & how to run

- Framework: `pytest` (8.4.2). Tests are synchronous (an asyncio plugin is present but unused). No pytest config file beyond `.pytest_cache`.
- Run from the repo root (per README):

```bash
cd ContextIQ
pytest backend/tests/ -v
```

Or from `backend/`:

```bash
cd backend
python3 -m pytest tests/ -v
```

- Auth tests spin up a `TestClient(app)` against a throwaway SQLite file (`tests/test_contextiq.db`, `tests/test_auth_security.db`), deleted and recreated at import time, with `get_db` overridden and the rate limiter reset per test.

## 2. Verified result

**58 passed** (this session, ~17s, Python 3.13.9). Zero failures, zero skips (audit §10).

## 3. Test files, counts, and coverage

| File | Test defs | Runtime cases | Area covered |
|---|---|---|---|
| `tests/test_auth.py` | 4 | 4 | Register success, duplicate-email `400`, login success, wrong-password `401`. |
| `tests/test_auth_security.py` | 7 | 7 | Password rules (short / missing upper / missing digit / missing special / valid), register + login rate-limit `429` after 5 attempts. |
| `tests/test_csv_compute.py` | 5 | 5 | Average aggregation, top-N, non-computational fallback to RAG, region named "NA" not silently dropped, multi-CSV-no-filename fallback. |
| `tests/test_document_loader_pdf.py` | 7 | 7 | Scanned-PDF detection heuristics (all-empty / normal / mostly-empty / empty input), clear actionable error, routing through `load_document`, normal PDF loads. |
| `tests/test_docx_compute.py` | 5 | 5 | Full-document summary uses complete text, exhaustive date extraction, non-full-document fallback, word count computed (not asked of LLM), too-large document declined. |
| `tests/test_md_compute.py` | 6 | 6 | Header hierarchy preserved as metadata, fenced-code `#` not treated as heading, full-document summary, fallback, heading list computed, too-large declined. |
| `tests/test_pdf_compute.py` | 8 | 8 | Summary, exhaustive extraction, fallback, exact page count, outline present/absent, too-large declined, scanned-PDF short-circuit. |
| `tests/test_sql_chain.py` | 11 | 20 (parametrized) | `OperationalError` classification: MySQL connection-lost by errno/message, MySQL-only, per-DB timeout recognition, timeout ≠ connection-lost, unrecognized passthrough, and `execute_query` wiring. |

**Total: 58 runtime cases.** (`test_sql_chain.py` expands to 20 via `@pytest.mark.parametrize`.)

## 4. What is tested well

- Auth surface end-to-end through the real app (register/login/rate-limit/password policy).
- The per-file-type compute paths (CSV/DOCX/PDF/MD) — aggregation correctness, structural-fact computation, full-document summarize/extract, too-large refusals, and fallback-to-RAG behavior.
- Scanned-PDF detection.
- Text-to-SQL error classification (the intermittent-`502` fix).

## 5. Untested areas (honest gaps)

From audit §10:

- **Route-layer integration:** `/chat/ask` end-to-end, conversation CRUD routes, document upload/list/delete routes, databases routes (`create`/`list`/`delete`/`ask`).
- **RAG pipeline end-to-end:** `run_rag_chain`, `hybrid_retriever`, `metadata_filter`, `query_rewriter`, and `ingestion/*` (chunking/embeddings/vector_store/keyword_store).
- **Text-to-SQL happy path:** only `OperationalError` classification is tested — `validate_sql`, execution over a real DB, and `summarize_answer` are not.
- **Crypto:** `utils/crypto` round-trip is not unit-tested.
- **Ownership/isolation dependencies:** `get_owned_conversation`, `get_owned_connection` not directly unit-tested (exercised only indirectly).
- **Entire frontend:** no test runner is configured; there are no `*.test.*` / `*.spec.*` files.

## 6. Suggested test additions (priority order)

1. Route integration tests for chat/conversations/documents/databases (auth + ownership + error codes).
2. `validate_sql` unit tests (forbidden keywords, stacked queries, SELECT-only) and a `crypto` round-trip test.
3. A RAG end-to-end test against a tiny fixture index (the eval harness already ingests one).
4. A minimal frontend test setup (Vitest) for the API client's error normalization and route guards.

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
