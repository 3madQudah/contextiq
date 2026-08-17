# 03 — Technical Specification

Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §2, §3, §4, §11.

Related: [04 — Architecture](04-ARCHITECTURE.md) · [05 — Data Model](05-DATA-MODEL.md) · [14 — Deployment](14-DEPLOYMENT.md)

---

## 1. Stack overview

| Layer | Technology |
|---|---|
| Backend framework | FastAPI (Uvicorn ASGI) |
| ORM / DB | SQLAlchemy; SQLite default, Postgres/MySQL supported |
| Auth | JWT (python-jose), passlib/bcrypt, slowapi rate limiting |
| Retrieval | FAISS (`faiss-cpu`) + BM25 (`rank_bm25`) via LangChain `EnsembleRetriever` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace) |
| LLM inference | Groq (`langchain-groq`), default model `llama-3.1-8b-instant` |
| Document loading | pypdf, python-docx, LangChain community loaders |
| Data compute | pandas |
| Encryption | `cryptography` (Fernet) |
| Frontend | React 18 + Vite, Tailwind CSS, axios, react-router-dom, react-markdown |

## 2. Backend dependencies (exact pins, `backend/requirements.txt`)

| Package | Version | Package | Version |
|---|---|---|---|
| fastapi | 0.135.2 | langchain-text-splitters | 1.1.1 |
| uvicorn | 0.42.0 | langchain-groq | 1.1.3 |
| pydantic | 2.13.4 | langchain-huggingface | 1.2.2 |
| python-multipart | 0.0.22 | rank_bm25 | 0.2.2 |
| python-jose | 3.5.0 | faiss-cpu | 1.13.2 |
| passlib[bcrypt] | 1.7.4 | sentence-transformers | 5.3.0 |
| bcrypt | <4.1 | pypdf | 6.14.2 |
| email-validator | 2.3.0 | python-docx | 1.2.0 |
| cryptography | 46.0.3 | pandas | 2.3.3 |
| slowapi | 0.1.10 | python-dotenv | 1.1.0 |
| sqlalchemy | 2.0.43 | pytest | 8.4.2 (dev) |
| psycopg2-binary | 2.9.12 | langchain | 1.2.14 |
| PyMySQL | 1.1.2 | langchain-core | 1.5.2 |
| langchain-community | 0.4.1 | langchain-classic | 1.0.3 |

**Python version:** README states "3.11+"; the backend `Dockerfile` pins `python:3.11-slim`. The test suite in this session ran on Python 3.13.9 and passed. No `pyproject.toml`; the exact minimum beyond "3.11+" is not otherwise specified.

> `bcrypt` is pinned `<4.1` because passlib 1.7.4 reads a `__about__` attribute removed in bcrypt ≥ 4.1.
>
> Stale note: `eval/README.md` references `docx2txt`, but current code uses `python-docx` (`load_docx_by_section`) and `docx2txt` is **not** a dependency.

## 3. Frontend dependencies (`frontend/package.json`)

**dependencies:** `@tabler/icons-react ^3.46.0`, `axios ^1.6.0`, `framer-motion ^11.0.0`, `lucide-react ^0.344.0`, `motion ^13.0.0`, `react ^18.2.0`, `react-dom ^18.2.0`, `react-markdown ^9.0.0`, `react-router-dom ^6.22.0`, `remark-gfm ^4.0.0`.

**devDependencies:** `@vitejs/plugin-react ^4.2.0`, `autoprefixer ^10.4.0`, `postcss ^8.4.0`, `tailwindcss ^3.4.0`, `vite ^5.1.0`.

**Node version:** README states "18+"; the frontend build image is `node:20-slim`. No `engines`/`.nvmrc`.

**Scripts:** `dev` → `vite`, `build` → `vite build`, `preview` → `vite preview`.

> Both `framer-motion` (^11) and `motion` (^13) are present and imported by different components (audit §2.2).

## 4. Environment variables

Every variable read anywhere in the code (audit §3.1). **Never commit real values** — see [13 — Security](13-SECURITY.md).

| Variable | Read in | Default | Required? | Purpose |
|---|---|---|---|---|
| `SECRET_KEY` | `auth/jwt_handler.py` | `"insecure-dev-secret-change-me"` | Yes in practice (insecure default) | JWT signing secret |
| `ALGORITHM` | `auth/jwt_handler.py` | `"HS256"` | No | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `auth/jwt_handler.py` | `"60"` | No | Access-token lifetime (minutes) |
| `DATABASE_URL` | `auth/database.py` | `"sqlite:///./contextiq.db"` | No | App DB connection string |
| `DB_ENCRYPTION_KEY` | `utils/crypto.py` | none | Yes for text-to-SQL | Fernet key encrypting saved connection strings |
| `GROQ_API_KEY` | `rag_chain.py`, `sql_chain.py`, `query_rewriter.py`, `{csv,docx,pdf,md}_compute.py` | none | Yes for any LLM answer | Groq API key |
| `GROQ_MODEL_NAME` | `rag_chain.py`, `sql_chain.py`, `{csv,docx,pdf,md}_compute.py` | `"llama-3.1-8b-instant"` | No | Main answering / SQL / phrasing model |
| `GROQ_REWRITE_MODEL_NAME` | `query_rewriter.py` | `"llama-3.1-8b-instant"` | No | Follow-up-rewrite model |
| `FRONTEND_ORIGIN` | `main.py` | `"http://localhost:5173"` | No | Single CORS allowed origin |
| `TOKENIZERS_PARALLELISM` | `eval/run_eval.py` | set `"false"` | No | Silence HF tokenizers warning in eval |
| `VITE_API_BASE_URL` | `frontend/src/services/api.js` | `"http://localhost:8000"` | No | Backend base URL, inlined at build time |
| `DOCKER_DATABASE_URL` | `docker-compose.yml` | → `sqlite:////app/data/contextiq.db` | No | Override backend container `DATABASE_URL` |
| `HF_HOME` | `backend/Dockerfile` | `/opt/hf_cache` | No (Docker) | Embedding-model cache location |

## 5. Module responsibilities (backend)

| Package | Responsibility |
|---|---|
| `api/` | FastAPI route handlers + shared dependencies (`get_current_user`, ownership) |
| `auth/` | User accounts, JWT, password hashing, **all ORM models**, DB engine/session (`database.py`) |
| `chain/` | RAG orchestration, hybrid retrieval, query rewriting, metadata filtering, text-to-SQL, per-file-type compute paths + classifiers |
| `ingestion/` | Chunking, embeddings, FAISS store, BM25/keyword store |
| `loaders/` | File loading, scanned-PDF detection, section-aware DOCX/MD |
| `prompt_eng/` | Prompt templates + `PROMPT_REGISTRY` |
| `utils/` | Fernet crypto, rate limiter, file helpers |
| `tests/` | Pytest suite |
| `data/` | Runtime storage (`raw/<user_id>/`, `vector_index/<user_id>/`) |

Application assembly, middleware order, and request lifecycle: see [04 — Architecture](04-ARCHITECTURE.md).

## 6. Retrieval constants

| Constant | Value | Location |
|---|---|---|
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | `ingestion/embeddings.py` |
| Chunk size / overlap | 1000 / 150 | `ingestion/chunking.py` |
| Ensemble weights (FAISS / BM25) | 0.5 / 0.5 | `chain/hybrid_retriever.py` |
| Per-retriever k | 8 | `chain/hybrid_retriever.py` |
| Fetch K (post-retrieval) | 8 | `chain/rag_chain.py` |
| Top K (kept) | 4 | `chain/rag_chain.py` |
| History turns | 3 pairs | `chain/query_rewriter.py` |
| Full-document char cap | 24,000 | `chain/{docx,pdf,md}_compute.py` |
| SQL row cap / timeout | 200 rows / 10s | `chain/sql_chain.py` |
| Schema cache TTL | 60s | `chain/sql_chain.py` |
| LLM temperature | 0 (all calls) | chain/compute modules |

## 7. Retrieval evaluation

Full methodology and results from audit §11. The harness (`eval/`) measures **retrieval quality only** (not answer quality) across three configurations — FAISS-only, BM25-only, Ensemble (Hybrid) — using the app's real retriever/ingestion functions (read-only with respect to app code).

### 7.1 Methodology

- **Corpus:** synthetic 10-document / ~17-chunk fixture (2 documents per file type) ingested into eval user `9001` via the real pipeline (`build_eval_corpus.py`).
- **Question set:** 28 labeled questions with ground-truth `relevant_chunk_ids` (`eval_set.json`, all `verified: true`), categorized `exact_number` / `rare_term`.
- **Metrics:** Precision@K, Recall@K, MRR, MAP, latency p50/p95, and Recall@K by category. **K = 4** (`config.py`).
- **Latency** includes retriever construction (indexes rebuilt per call, no caching) plus retrieval; one untimed warm-up per config absorbs one-time model-load cost.

### 7.2 Results (`eval/results.md`, generated 2026-08-07, 28 questions, 17 chunks, K=4)

| Metric | FAISS-only | BM25-only | Ensemble (Hybrid) |
|---|---|---|---|
| Precision@K | 25.0% | 22.3% | 25.0% |
| Recall@K | 100.0% | 89.3% | 100.0% |
| MRR | 0.964 | 0.869 | 0.893 |
| MAP | 0.964 | 0.869 | 0.893 |
| Latency p50 (ms) | 12.2 | 0.7 | 12.4 |
| Latency p95 (ms) | 44.6 | 0.8 | 13.6 |

Recall@K by category (FAISS / BM25 / Hybrid): `exact_number` 100.0 / 87.5 / 100.0; `rare_term` 100.0 / 91.7 / 100.0.

**Finding:** BM25-only misses three exact-value questions (q04, q14, q15) that the hybrid retriever recovers (+12.0% recall vs BM25-only).

### 7.3 Weight sweep (`eval/weight_tuning_summary.md`, K=4)

| Weights (FAISS/BM25) | Precision@4 | Recall@4 | MRR | MAP |
|---|---|---|---|---|
| 0.5 / 0.5 (default) | 25.0% | 100.0% | 0.893 | 0.893 |
| 0.6 / 0.4 | 25.0% | 100.0% | 0.899 | 0.899 |
| 0.7 / 0.3 | 25.0% | 100.0% | 0.899 | 0.899 |
| 0.8 / 0.2 | 25.0% | 100.0% | 0.899 | 0.899 |

Precision/Recall are identical across all weightings. MRR/MAP move by a single step (+0.006) once FAISS ≥ 0.6, driven by exactly one question (q04) re-ranking 3→2. **Decision: keep 0.5/0.5** — a one-question effect on a 17-chunk corpus is not a generalizable signal. The default in `hybrid_retriever.py` is unchanged.

### 7.4 Stated caveat

From `eval_set.json._meta.READ_ME_BEFORE_CITING`: the corpus is a tiny synthetic fixture. Numbers are **illustrative of hybrid-vs-single-retriever behavior, not a production-scale benchmark**. Note `_meta.top_k` reads 5, but the harness runs at K=4 (`config.py`), and all recorded results were generated at K=4.

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
