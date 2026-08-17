# ContextIQ — Project Audit

> Read-only factual inventory produced by reading every source file in the repository. Scope: the ContextIQ application only. The large `.claude/skills/` tree in the repo root is Claude Code editor tooling (design/brand/UI skill packs), **not** part of the ContextIQ product, and is deliberately excluded from this audit. Anything not found in the repo is marked `UNKNOWN — not found in repo`.

Audit date: 2026-08-17 · Branch: `main` · All 58 backend tests pass (verified, see §10).

---

## 1. REPOSITORY MAP

### 1.1 Top-level layout

```
ContextIQ/
├── README.md                 Project overview, setup, features, evaluation, deployment (planned)
├── PROJECT_TREE.md           Human-authored annotated tree (documentation only)
├── .env.example              Template for backend/.env (CONTAINS REAL-LOOKING SECRET VALUES — see §7)
├── .gitignore
├── docker-compose.yml        Two-service (backend+frontend) container stack
├── contextiq.db              SQLite app DB (gitignored; present locally at repo root)
├── backend/                  FastAPI application (Python)
├── frontend/                 React + Vite single-page app
├── eval/                     Retrieval evaluation harness + synthetic fixtures + results
└── docs/                     This audit
```

Generated/ignored dirs excluded from the map: `node_modules/`, `.git/`, `__pycache__/`, `.pytest_cache/`, `frontend/dist/`, FAISS binaries under `backend/data/`.

### 1.2 Backend source files (`backend/`)

Line counts are exact (`wc -l`).

| Path | Lines | Purpose |
|---|---|---|
| `main.py` | 54 | FastAPI entrypoint: loads env, `create_all()`, CORS, slowapi limiter/middleware, mounts 5 routers, `/health`. |
| `requirements.txt` | 46 | Pinned Python dependencies. |
| `api/__init__.py` | 1 | Package marker. |
| `api/auth_routes.py` | 39 | `/register`, `/login` (rate-limited, JWT issuance). |
| `api/chat_routes.py` | 141 | `/ask` — routes each question to CSV-compute / full-doc / RAG; persists messages. |
| `api/conversations_routes.py` | 127 | List/create/get/rename/delete conversations. |
| `api/databases_routes.py` | 163 | Register/list/delete external DB connections; `/{id}/ask` text-to-SQL. |
| `api/dependencies.py` | 106 | `get_current_user` (JWT), ownership dependencies for conversations & connections. |
| `api/documents_routes.py` | 82 | Upload/list/delete documents; triggers ingestion. |
| `auth/__init__.py` | 1 | Package marker. |
| `auth/auth_handler.py` | 47 | Password hashing (passlib/bcrypt), `register_user`, `authenticate_user`. |
| `auth/chat_models.py` | 63 | ORM: `Conversation`, `Message`. |
| `auth/database.py` | 43 | SQLAlchemy engine/session, `Base`, `get_db`, postgres:// normalization. |
| `auth/db_connection_models.py` | 39 | ORM: `DatabaseConnection`. |
| `auth/jwt_handler.py` | 35 | `create_access_token` / `decode_access_token` (python-jose). |
| `auth/models.py` | 37 | ORM: `User`. |
| `auth/schemas.py` | 82 | Pydantic schemas + password-strength validator. |
| `chain/__init__.py` | 4 | Package marker. |
| `chain/csv_compute.py` | 381 | Exact pandas aggregation path for CSV. |
| `chain/csv_query_classifier.py` | 37 | Regex gate: is a CSV question computational? |
| `chain/docx_compute.py` | 355 | Full-document DOCX path (structural facts + summarize/extract). |
| `chain/docx_query_classifier.py` | 52 | Regex gate: does a DOCX question need the whole document? |
| `chain/hybrid_retriever.py` | 39 | Builds FAISS+BM25 `EnsembleRetriever`. |
| `chain/md_compute.py` | 290 | Full-document Markdown path. |
| `chain/md_query_classifier.py` | 39 | Regex gate for Markdown. |
| `chain/metadata_filter.py` | 28 | Post-retrieval filter by `file_type`/`file_name`. |
| `chain/pdf_compute.py` | 373 | Full-document PDF path. |
| `chain/pdf_query_classifier.py` | 51 | Regex gate for PDF. |
| `chain/query_rewriter.py` | 64 | LLM rewrite of conversational follow-ups → standalone query. |
| `chain/rag_chain.py` | 125 | Core RAG pipeline. |
| `chain/sql_chain.py` | 614 | Text-to-SQL pipeline (introspect → generate → validate → execute read-only → summarize). |
| `ingestion/__init__.py` | 1 | Package marker. |
| `ingestion/chunking.py` | 33 | `RecursiveCharacterTextSplitter` + metadata tagging. |
| `ingestion/embeddings.py` | 17 | Cached HuggingFace embeddings singleton. |
| `ingestion/keyword_store.py` | 69 | BM25 retriever + `chunks.pkl` persistence. |
| `ingestion/vector_store.py` | 77 | FAISS build/load/rebuild per user. |
| `loaders/__init__.py` | 1 | Package marker. |
| `loaders/document_loader.py` | 233 | Per-type loaders; scanned-PDF detection; section-aware DOCX/MD. |
| `prompt_eng/__init__.py` | 28 | `PROMPT_REGISTRY`. |
| `prompt_eng/base_prompt.py` | 43 | Shared `BASE_INSTRUCTIONS`, `ANSWER_SECTION`, `DEFAULT_PROMPT_TEMPLATE`. |
| `prompt_eng/csv_prompt.py` | 44 | CSV RAG prompt. |
| `prompt_eng/docx_prompt.py` | 38 | DOCX RAG prompt. |
| `prompt_eng/md_prompt.py` | 35 | Markdown RAG prompt. |
| `prompt_eng/pdf_prompt.py` | 41 | PDF RAG prompt. |
| `prompt_eng/sql_prompt.py` | 49 | Text-to-SQL generation + answer-summary prompts. |
| `prompt_eng/txt_prompt.py` | 27 | Plain-text RAG prompt. |
| `utils/__init__.py` | 1 | Package marker. |
| `utils/crypto.py` | 40 | Fernet encrypt/decrypt of connection strings. |
| `utils/helpers.py` | 15 | Supported-extension check. |
| `utils/rate_limit.py` | 34 | slowapi `Limiter` + 429 handler. |
| `tests/__init__.py` | 1 | Package marker. |
| `tests/test_auth.py` | 123 | Register/login/token tests (4). |
| `tests/test_auth_security.py` | 122 | Password-strength + rate-limit tests (7). |
| `tests/test_csv_compute.py` | 113 | CSV compute tests (5). |
| `tests/test_document_loader_pdf.py` | 95 | Scanned-PDF detection tests (7). |
| `tests/test_docx_compute.py` | 145 | DOCX full-doc tests (5). |
| `tests/test_md_compute.py` | 152 | Markdown full-doc tests (6). |
| `tests/test_pdf_compute.py` | 211 | PDF full-doc tests (8). |
| `tests/test_sql_chain.py` | 177 | SQL error-classification tests (11 defs → 20 with parametrization). |

Backend source (excl. tests/pycache): **~4,240 lines**; total incl. tests **5,477 lines**.

### 1.3 Frontend source files (`frontend/src/`)

| Path | Lines | Purpose |
|---|---|---|
| `main.jsx` | 28 | Root render; wraps App in MotionConfig/BrowserRouter/Theme/Auth/Toast providers. |
| `App.jsx` | 48 | Route table (see §9.1). |
| `index.css` | 204 | Tailwind layers + design tokens (CSS vars) + component classes. |
| `services/api.js` | 151 | Single axios client; token storage; every endpoint wrapper. |
| `context/AuthContext.jsx` | 94 | Session state (token+user in localStorage). |
| `context/AppDataContext.jsx` | 107 | Shared conversations/documents/DB-connections state. |
| `context/ThemeContext.jsx` | 35 | Light/dark theme, persisted. |
| `context/ToastContext.jsx` | 49 | App-wide toast queue. |
| `pages/Landing.jsx` | 299 | Marketing landing page. |
| `pages/Login.jsx` | 87 | Login form. |
| `pages/Register.jsx` | 148 | Registration form + password meter. |
| `pages/Chat.jsx` | 208 | Document chat view. |
| `pages/Documents.jsx` | 223 | Upload/list/delete documents. |
| `pages/Databases.jsx` | 243 | DB connections list + add form. |
| `pages/DatabaseQuery.jsx` | 150 | Ask-a-database view (session-only history). |
| `pages/marketing/Product.jsx` | 76 | `/product` content page. |
| `pages/marketing/Databases.jsx` | 71 | `/databases` (public) content page. |
| `pages/marketing/Docs.jsx` | 177 | `/docs` API reference page. |
| `components/AppLayout.jsx` | 74 | Authed shell: sidebar + mobile drawer + `<Outlet/>`. |
| `components/Sidebar.jsx` | 237 | Conversation list, nav, user footer, rename/delete. |
| `components/Composer.jsx` | 74 | Auto-growing message input. |
| `components/MessageBubble.jsx` | 41 | User/assistant chat bubble + sources. |
| `components/DatabaseAnswer.jsx` | 37 | SQL answer + SQL code + results table. |
| `components/ResultsTable.jsx` | 32 | Renders SQL result rows/cols. |
| `components/CodeBlock.jsx` | 32 | SQL code block with copy button. |
| `components/Markdown.jsx` | 10 | `react-markdown` + `remark-gfm` wrapper. |
| `components/SourceChip.jsx` | 15 | Clickable source-file filter chip. |
| `components/Dropzone.jsx` | 65 | Drag/drop + click file picker. |
| `components/ConfirmDialog.jsx` | 61 | Modal confirm (delete flows). |
| `components/Button.jsx` | 39 | Button w/ 5 variants + loading. |
| `components/TextInput.jsx` | 32 | Labeled text input. |
| `components/PasswordInput.jsx` | 49 | Password input + show/hide. |
| `components/Select.jsx` | 26 | Labeled select. |
| `components/PasswordStrengthMeter.jsx` | 46 | Live password rule checklist + `isPasswordValid`. |
| `components/EmptyState.jsx` | 10 | Empty-state card. |
| `components/FullPageSpinner.jsx` | 9 | Full-screen loading spinner. |
| `components/TypingIndicator.jsx` | 9 | Animated "assistant typing" dots. |
| `components/ThemeToggle.jsx` | 33 | Light/dark toggle button. |
| `components/Logo.jsx` | 23 | In-app brand mark (Sidebar/mobile header). |
| `components/AuroraBackground.jsx` | 20 | Decorative gradient blobs (marketing/auth). |
| `components/PipelineDiagram.jsx` | 397 | Landing-hero animated SVG fan-in pipeline. |
| `components/ToastViewport.jsx` | 60 | Renders toast queue. |
| `components/ProtectedRoute.jsx` | 12 | Gate: requires auth. |
| `components/PublicOnlyRoute.jsx` | 13 | Gate: bounces authed users to `/app`. |
| `components/landing/AuthBrand.jsx` | 16 | Brand mark for auth pages. |
| `components/landing/BrainMark.jsx` | 42 | SVG brain logo (exports paths for PipelineDiagram). |
| `components/landing/ChatMockup.jsx` | 54 | Static illustrative chat card. |
| `components/landing/PublicNav.jsx` | 55 | Shared public-site nav. |
| `components/landing/PublicFooter.jsx` | 62 | Shared public-site footer (contact links). |
| `components/landing/StepList.jsx` | 53 | Shared numbered-step layout (Product/Databases). |
| `lib/fileTypes.js` | 24 | Accepted extensions, icons, extension helpers. |
| `lib/databaseTypes.js` | 9 | DB-type labels. |
| `lib/jwt.js` | 18 | Client-side JWT payload decode (no verify). |
| `lib/titles.js` | 21 | Heuristic conversation-title generator. |
| `lib/user.js` | 30 | Display name / initials from user. |
| `lib/motion.js` | 45 | Shared framer-motion animation tokens. |

Frontend source total: **4,283 lines**.

### 1.4 Eval files (`eval/`)

| Path | Lines | Purpose |
|---|---|---|
| `run_eval.py` | 433 | Runs FAISS-only/BM25-only/Hybrid; computes IR metrics; writes results. |
| `build_eval_corpus.py` | 82 | One-time ingest of `fixtures/` into eval user 9001. |
| `config.py` | 9 | `EVAL_USER_ID = 9001`, `TOP_K = 4`. |
| `eval_set.json` | 267 | 28 labeled questions w/ ground-truth chunk ids + `_meta`. |
| `README.md` | — | Eval harness docs. |
| `weight_tuning_summary.md` | 55 | FAISS/BM25 weight sweep summary. |
| `results.md` / `results.json` | — | Baseline run (K=4, 28 q, 17 chunks). |
| `results_baseline_k4.{md,json}` | — | Baseline results. |
| `results_weights_0.6_0.4.{md,json}` | — | Weight-sweep run. |
| `results_weights_0.7_0.3.{md,json}` | — | Weight-sweep run. |
| `results_weights_0.8_0.2.{md,json}` | — | Weight-sweep run. |
| `fixtures/*` | — | 10 synthetic source docs (2 per file type). |
| `fixtures/source/*` | — | 4 plaintext originals for PDF/DOCX conversions (not read by scripts). |

### 1.5 Dead / orphaned artifacts observed

- `backend/data/vector_index/3/` exists **but `backend/data/raw/3/` does not** — an orphaned FAISS index for a user with no raw uploads on disk. Confirmed via directory listing. (Data artifact, not code.)
- `backend/tests/test_contextiq.db` and `backend/tests/test_auth_security.db` — leftover SQLite files created by tests (both test modules delete/recreate at import time; safe to ignore).
- `contextiq.db` present at both repo root and `backend/` (both gitignored). The app default `DATABASE_URL` is `sqlite:///./contextiq.db` (cwd-relative), so which one is used depends on the process cwd.
- No dead **code** modules were identified; every backend module is imported by another (verified by tracing imports from `main.py`, `chat_routes.py`, `databases_routes.py`, and the eval scripts).

---

## 2. TECH STACK & DEPENDENCIES

### 2.1 Backend

- **Python version:** README states "Python 3.11+"; the backend `Dockerfile` pins `python:3.11-slim`. Tests in this audit were run under Python **3.13.9** (local anaconda) and pass. No `pyproject.toml`; no `.python-version` file. `UNKNOWN` — exact minimum beyond "3.11+".
- **Dependencies (`backend/requirements.txt`, exact pins):**

| Package | Version | Group |
|---|---|---|
| fastapi | 0.135.2 | Web framework |
| uvicorn | 0.42.0 | ASGI server |
| pydantic | 2.13.4 | Validation |
| python-multipart | 0.0.22 | File uploads |
| python-jose | 3.5.0 | JWT |
| passlib[bcrypt] | 1.7.4 | Password hashing |
| bcrypt | <4.1 | Pinned below 4.1 (passlib 1.7.4 incompatibility) |
| email-validator | 2.3.0 | `EmailStr` |
| cryptography | 46.0.3 | Fernet encryption |
| slowapi | 0.1.10 | Rate limiting |
| sqlalchemy | 2.0.43 | ORM |
| psycopg2-binary | 2.9.12 | Postgres driver |
| PyMySQL | 1.1.2 | MySQL driver |
| langchain | 1.2.14 | LLM framework |
| langchain-core | 1.5.2 | — |
| langchain-community | 0.4.1 | FAISS/BM25/loaders |
| langchain-classic | 1.0.3 | `EnsembleRetriever` |
| langchain-text-splitters | 1.1.1 | Chunking |
| langchain-groq | 1.1.3 | Groq LLM client |
| langchain-huggingface | 1.2.2 | Embeddings |
| rank_bm25 | 0.2.2 | BM25 |
| faiss-cpu | 1.13.2 | Vector index |
| sentence-transformers | 5.3.0 | Embedding model runtime |
| pypdf | 6.14.2 | PDF loading |
| python-docx | 1.2.0 | DOCX loading |
| pandas | 2.3.3 | CSV compute |
| python-dotenv | 1.1.0 | `.env` loading |
| pytest | 8.4.2 | Tests (dev only) |

> Note: `eval/README.md` mentions `docx2txt` was needed for an older DOCX loader path, but the code now uses `python-docx` via `load_docx_by_section()` (no `Docx2txtLoader`), and `docx2txt` is **not** in `requirements.txt`. That note is stale relative to current code.

### 2.2 Frontend

- **Node version:** README states "Node.js 18+"; `frontend/Dockerfile` builds with `node:20-slim`. No `.nvmrc`/`engines` field. `UNKNOWN` — exact required version beyond "18+".
- **`package.json`** — name `contextiq-frontend`, version `0.1.0`, `type: module`, `private: true`.

**dependencies:**

| Package | Version |
|---|---|
| @tabler/icons-react | ^3.46.0 |
| axios | ^1.6.0 |
| framer-motion | ^11.0.0 |
| lucide-react | ^0.344.0 |
| motion | ^13.0.0 |
| react | ^18.2.0 |
| react-dom | ^18.2.0 |
| react-markdown | ^9.0.0 |
| react-router-dom | ^6.22.0 |
| remark-gfm | ^4.0.0 |

**devDependencies:**

| Package | Version |
|---|---|
| @vitejs/plugin-react | ^4.2.0 |
| autoprefixer | ^10.4.0 |
| postcss | ^8.4.0 |
| tailwindcss | ^3.4.0 |
| vite | ^5.1.0 |

> Note: both `framer-motion` (^11) and `motion` (^13) are present; components import from both (`framer-motion` in MessageBubble/DatabaseAnswer/ConfirmDialog/AppLayout, `motion/react` in Button/ThemeToggle/Sidebar/ToastViewport/marketing).

### 2.3 Build / run scripts

- **Frontend `package.json` scripts:** `dev` → `vite`; `build` → `vite build`; `preview` → `vite preview`.
- **Backend:** no Makefile, no shell scripts, no console-entry scripts. Run via `uvicorn main:app --reload` (README). Tests via `pytest backend/tests/ -v`.
- **Eval:** `python3 build_eval_corpus.py` then `python3 run_eval.py` (run from `eval/`).
- No `Makefile` anywhere in the app tree. No top-level shell scripts.

---

## 3. CONFIGURATION & ENVIRONMENT

### 3.1 Environment variables (every one read in code)

| Variable | Read in | Default | Required? | Controls |
|---|---|---|---|---|
| `SECRET_KEY` | `auth/jwt_handler.py:16` | `"insecure-dev-secret-change-me"` | Recommended (insecure default) | JWT signing secret. |
| `ALGORITHM` | `auth/jwt_handler.py:17` | `"HS256"` | No | JWT algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `auth/jwt_handler.py:18` | `"60"` (int) | No | Access-token lifetime. |
| `DATABASE_URL` | `auth/database.py:18` | `"sqlite:///./contextiq.db"` | No | App DB connection (SQLite/Postgres). `postgres://`→`postgresql://` normalized. |
| `DB_ENCRYPTION_KEY` | `utils/crypto.py:18` | none | Required for text-to-SQL (RuntimeError if unset when used) | Fernet key encrypting saved connection strings. |
| `GROQ_API_KEY` | `chain/rag_chain.py:29`, `sql_chain.py:45`, `query_rewriter.py:19`, `csv/docx/pdf/md_compute.py` | none | Required for any LLM answer | Groq API key. |
| `GROQ_MODEL_NAME` | `rag_chain.py:30`, `sql_chain.py:46`, `csv/docx/pdf/md_compute.py` | `"llama-3.1-8b-instant"` | No | Main answering/SQL/phrasing model. |
| `GROQ_REWRITE_MODEL_NAME` | `chain/query_rewriter.py:25` | `"llama-3.1-8b-instant"` | No | Follow-up-rewrite model (kept separate from the answering model). |
| `FRONTEND_ORIGIN` | `main.py:29` | `"http://localhost:5173"` | No | CORS allowed origin (single). |
| `TOKENIZERS_PARALLELISM` | `eval/run_eval.py:33` | set to `"false"` via `setdefault` | No | Silences HF tokenizers fork warning during eval. |
| `VITE_API_BASE_URL` | `frontend/src/services/api.js:3` | `"http://localhost:8000"` | No | Backend base URL, inlined at Vite build time. |
| `DOCKER_DATABASE_URL` | `docker-compose.yml` only | unset → `sqlite:////app/data/contextiq.db` | No | Override for the backend container's `DATABASE_URL`. |
| `HF_HOME` | `backend/Dockerfile` (ENV) | `/opt/hf_cache` | No (Docker) | Pins embedding-model cache location for pre-bake. |

`GROQ_API_KEY` / `GROQ_MODEL_NAME` are read identically in all six chain/compute modules; `test_connection` and schema/exec use only `GROQ_MODEL_NAME` in `sql_chain`.

### 3.2 `.env.example` (variable names only; values `<redacted>`)

`.env.example` defines: `SECRET_KEY=<redacted>`, `ALGORITHM=HS256`, `ACCESS_TOKEN_EXPIRE_MINUTES=60`, `DATABASE_URL=sqlite:///./contextiq.db` (with a commented Postgres alternative), `DB_ENCRYPTION_KEY=<redacted>`, `GROQ_API_KEY=<redacted>`, `FRONTEND_ORIGIN=http://localhost:5173`, `VITE_API_BASE_URL=http://localhost:8000`, and a commented `DOCKER_DATABASE_URL=`.

> **SECURITY FLAG:** `.env.example` contains **real-looking, non-placeholder secret values** for `SECRET_KEY`, `DB_ENCRYPTION_KEY`, and `GROQ_API_KEY` (they look like a genuine Fernet key and a `gsk_...` Groq key), not `changeme`-style placeholders. This file is committed to git. See §7 and §14. (Actual values not reproduced here.)

`frontend/.env.example` contains only `VITE_API_BASE_URL=http://localhost:8000`.

### 3.3 Config files

| File | Configures |
|---|---|
| `frontend/vite.config.js` | Vite + `@vitejs/plugin-react`; no dev proxy (axios hits `VITE_API_BASE_URL` directly). |
| `frontend/tailwind.config.js` | `darkMode: "class"`; **replaces** `fontSize`/`fontWeight` scales (enforces "two weights, six sizes"); extends colors (CSS-var driven), radius, shadows, keyframes/animations (aurora, shimmer, pipeline). |
| `frontend/postcss.config.js` | `tailwindcss` + `autoprefixer`. |
| `frontend/nginx.conf` | SPA fallback (`try_files … /index.html`), 1y immutable cache for `/assets/`, `/healthz` → 200. |
| `frontend/index.html` | Vite HTML entry (not separately read; standard). |
| `backend/Dockerfile` | 2-stage build; pre-downloads embedding model; runtime as non-root `appuser`; healthcheck. |
| `frontend/Dockerfile` | 2-stage Node build → nginx serve; `VITE_API_BASE_URL` build ARG. |
| `docker-compose.yml` | backend+frontend services, `backend_data` named volume, healthchecks, networks. |
| `backend/.dockerignore`, `frontend/.dockerignore` | Exclude data/secrets/venv/node_modules from image context. |
| **No** `alembic.ini` / migrations | Schema created via `Base.metadata.create_all()` (see §6.3). |

---

## 4. BACKEND ARCHITECTURE

### 4.1 Entry point & assembly (`backend/main.py`)

1. `load_dotenv()`.
2. Imports `auth.chat_models`, `auth.db_connection_models`, `auth.models` (registers all ORM tables on the shared `Base.metadata`).
3. `Base.metadata.create_all(bind=engine)` — creates tables on startup if missing (no migration tool).
4. `FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")`.
5. `app = FastAPI(title="ContextIQ")`.
6. `app.state.limiter = limiter`; registers `RateLimitExceeded` exception handler; adds `SlowAPIMiddleware`.
7. Adds `CORSMiddleware` (`allow_origins=[FRONTEND_ORIGIN]`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`).
8. Mounts routers with prefixes: `/api/auth`, `/api/documents`, `/api/chat`, `/api/conversations`, `/api/databases`.
9. `GET /health` → `{"status": "ok"}`.

There are **no** startup/shutdown event handlers beyond `create_all` at import time.

### 4.2 Middleware (execution order)

Registered order (FastAPI runs middleware in reverse-registration for the request path): `SlowAPIMiddleware` (added first), then `CORSMiddleware` (added second). The slowapi rate limiter is also enforced per-route via the `@limiter.limit(...)` decorator on auth routes. There is **no** custom auth middleware — auth is enforced per-route via the `get_current_user` dependency.

### 4.3 Modules / packages & responsibilities

- `api/` — FastAPI route handlers + shared dependencies.
- `auth/` — user accounts, JWT, password hashing, and **all** ORM models + the DB engine/session (`database.py`).
- `chain/` — RAG orchestration, hybrid retrieval, query rewriting, metadata filtering, text-to-SQL, and the per-file-type computational/full-document paths + their classifiers.
- `ingestion/` — chunking, embeddings, FAISS store, BM25/keyword store.
- `loaders/` — file loading + scanned-PDF detection + section-aware DOCX/MD.
- `prompt_eng/` — prompt templates + registry.
- `utils/` — Fernet crypto, rate limiter, file helpers.
- `tests/` — pytest suite.
- `data/` — runtime storage (`raw/<user_id>/`, `vector_index/<user_id>/`).

### 4.4 Request lifecycle (typical `POST /api/chat/ask`)

1. CORS + SlowAPI middleware run.
2. FastAPI resolves dependencies: `get_current_user` (decodes bearer JWT → loads `User`) and `get_db` (session).
3. `ask()` handler (`api/chat_routes.py`): if no `conversation_id`, creates+commits a `Conversation`; else `get_owned_conversation_by_id` (404 if not owned).
4. Builds `history` from last `DEFAULT_HISTORY_TURNS` (3) turn-pairs.
5. Persists the user `Message` (committed **before** the LLM call).
6. Routing (first non-None wins): CSV computational path → full-document path (DOCX/PDF/MD) → `run_rag_chain`.
7. On any exception → `502 Bad Gateway` (user message kept, no fabricated assistant message).
8. On success: persists assistant `Message` (with `sources`), bumps `conversation.updated_at`, commits.
9. Returns `ChatResponse` (`answer`, `sources`, `conversation_id`, `rewritten_query`).

### 4.5 Background tasks / schedulers

None. No Celery, APScheduler, threads, or async jobs. All work is synchronous within the request. (Client-side, the frontend serializes uploads — see §8.1 note — but that is browser-side, not a backend scheduler.)

---

## 5. API SPECIFICATION

Base: all routes are prefixed as mounted in `main.py`. Auth = "requires JWT" means the `get_current_user` dependency (HTTP Bearer). Error bodies are `{"detail": ...}`.

### 5.1 Endpoint table

| Method + Path | Handler (file) | Auth | Rate limit | Success |
|---|---|---|---|---|
| `GET /health` | `health_check` (`main.py`) | Public | none | 200 `{status:"ok"}` |
| `POST /api/auth/register` | `register` (`auth_routes.py`) | Public | `5/15minutes` per IP | 201 `UserResponse` |
| `POST /api/auth/login` | `login` (`auth_routes.py`) | Public | `5/15minutes` per IP | 200 `TokenResponse` |
| `POST /api/documents/upload` | `upload_document` (`documents_routes.py`) | JWT | none | 201 `{filename, chunks_indexed}` |
| `GET /api/documents/` | `list_documents` | JWT | none | 200 `{documents: [names]}` |
| `DELETE /api/documents/{file_name}` | `delete_document` | JWT | none | 200 `{filename, deleted, remaining_chunks}` |
| `POST /api/chat/ask` | `ask` (`chat_routes.py`) | JWT | none | 200 `ChatResponse` |
| `GET /api/conversations` | `list_conversations` | JWT | none | 200 `[ConversationSummary]` |
| `POST /api/conversations` | `create_conversation` | JWT | none | 201 `ConversationSummary` |
| `GET /api/conversations/{conversation_id}` | `get_conversation` | JWT (+ownership) | none | 200 `ConversationDetail` |
| `PATCH /api/conversations/{conversation_id}` | `rename_conversation` | JWT (+ownership) | none | 200 `ConversationSummary` |
| `DELETE /api/conversations/{conversation_id}` | `delete_conversation` | JWT (+ownership) | none | 204 |
| `POST /api/databases` | `create_connection` (`databases_routes.py`) | JWT | none | 201 `ConnectionSummary` |
| `GET /api/databases` | `list_connections` | JWT | none | 200 `[ConnectionSummary]` |
| `DELETE /api/databases/{connection_id}` | `delete_connection` | JWT (+ownership) | none | 204 |
| `POST /api/databases/{connection_id}/ask` | `ask_database` | JWT (+ownership) | none | 200 `DBQueryResponse` |

### 5.2 Per-endpoint detail

**`POST /api/auth/register`**
- Body `RegisterRequest`: `first_name: str` (req), `last_name: str` (req), `email: EmailStr` (req), `password: str` (req, validated by strength rules — §7.5).
- Success 201 `UserResponse`: `id:int, first_name, last_name, email:EmailStr, created_at:datetime`.
- Errors: `422` weak password (`PydanticCustomError` "password_too_weak" / email invalid); `400` "Email already registered"; `429` rate limit.

**`POST /api/auth/login`**
- Body `LoginRequest`: `email: EmailStr`, `password: str`.
- Success 200 `TokenResponse`: `access_token:str, token_type:"bearer"`.
- Errors: `401` "Incorrect email or password"; `422` invalid body; `429` rate limit.

**`POST /api/documents/upload`**
- Body: `multipart/form-data`, field `file` (`UploadFile`).
- Behavior: rejects unsupported ext; saves to `data/raw/{user_id}/{filename}`; `load_document` → `chunk_documents` → `build_faiss_index` → `save_chunks`.
- Success 201 `{filename, chunks_indexed:int}`.
- Errors: `400` "Unsupported file type. Allowed: .pdf, .docx, .txt, .csv, .md"; `422` `ScannedPDFError` (scanned/image PDF); `401` no/invalid token.

**`GET /api/documents/`** → 200 `{documents: sorted(os.listdir(user_dir))}` (empty list if no dir). `401` if unauth.

**`DELETE /api/documents/{file_name}`** — `file_name` path param (the natural key; no doc id table). Removes file, `remove_chunks_for_file`, `rebuild_faiss_index`. Success 200 `{filename, deleted:true, remaining_chunks:int}`. `404` "Document not found"; `401`.

**`POST /api/chat/ask`**
- Body `ChatRequest`: `question:str` (req), `conversation_id:int|null`, `file_type:str|null`, `file_name:str|null`.
- Success 200 `ChatResponse`: `answer:str, sources:List[str], conversation_id:int, rewritten_query:str|null`.
- Errors: `404` conversation not owned/not found (when `conversation_id` given); `502` "Failed to generate an answer. Please try again." (any pipeline exception); `401`.

**`GET /api/conversations`** → 200 `[ConversationSummary]` (`id,title,created_at,updated_at,message_count`), ordered by `updated_at desc`. `401`.

**`POST /api/conversations`** — Body `ConversationCreateRequest`: `title:str|null` (defaults to "New conversation"). 201 `ConversationSummary`. `401`.

**`GET /api/conversations/{conversation_id}`** — 200 `ConversationDetail` (summary + `messages:[MessageResponse{id,role,content,sources?,created_at}]`). `404` not owned; `401`.

**`PATCH /api/conversations/{conversation_id}`** — Body `ConversationRenameRequest`: `title:str` (req). 200 `ConversationSummary`. `404`; `401`; `422` missing title.

**`DELETE /api/conversations/{conversation_id}`** — 204. `404`; `401`.

**`POST /api/databases`**
- Body `ConnectionCreateRequest`: `name:str`, `db_type: Literal["postgresql","mysql","sqlite"]`, `connection_string:str`.
- Behavior: `test_connection()` (real connect + `SELECT 1`); on success stores encrypted string.
- Success 201 `ConnectionSummary`: `id,name,db_type,created_at`.
- Errors: `400` "Could not connect to the database: …" / malformed / db_type mismatch; `422` invalid `db_type`; `401`.

**`GET /api/databases`** → 200 `[ConnectionSummary]`, ordered `created_at desc`. `401`.

**`DELETE /api/databases/{connection_id}`** → 204. `404` not owned; `401`.

**`POST /api/databases/{connection_id}/ask`**
- Body `DBQueryRequest`: `question:str`.
- Success 200 `DBQueryResponse`: `answer:str, sql_query:str, columns:List[str], rows:List[list], row_count:int, truncated:bool`.
- Errors: `400` `SQLValidationError` → "Generated query was rejected ({layer}): …"; `504` `SQLExecutionTimeout`; `503` `SQLConnectionError`; `502` any other (unclassified); `404` not owned; `401`.

---

## 6. DATA MODEL

### 6.1 ORM tables (SQLAlchemy, declarative `Base` in `auth/database.py`)

**`users`** (`auth/models.py`, class `User`)

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, indexed |
| `first_name` | String | not null |
| `last_name` | String | not null |
| `email` | String | unique, indexed, not null |
| `hashed_password` | String | not null |
| `created_at` | DateTime(timezone=True) | default `now(utc)` |

Relationships: `conversations` (1→N, cascade all/delete-orphan), `database_connections` (1→N, cascade all/delete-orphan).

**`conversations`** (`auth/chat_models.py`, class `Conversation`)

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, indexed |
| `user_id` | Integer | FK `users.id` ON DELETE CASCADE, not null, indexed |
| `title` | String | not null |
| `created_at` | DateTime(tz=True) | default `now(utc)` |
| `updated_at` | DateTime(tz=True) | default `now(utc)`, `onupdate=now(utc)` |

Relationships: `user` (N→1); `messages` (1→N, cascade all/delete-orphan, ordered by `Message.created_at`).

**`messages`** (`auth/chat_models.py`, class `Message`)

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, indexed |
| `conversation_id` | Integer | FK `conversations.id` ON DELETE CASCADE, not null, indexed |
| `role` | String | not null ("user"/"assistant") |
| `content` | Text | not null |
| `sources` | JSON | nullable |
| `created_at` | DateTime(tz=True) | default `now(utc)` |

Relationship: `conversation` (N→1).

**`database_connections`** (`auth/db_connection_models.py`, class `DatabaseConnection`)

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, indexed |
| `user_id` | Integer | FK `users.id` ON DELETE CASCADE, not null, indexed |
| `name` | String | not null |
| `db_type` | String | not null ("postgresql"/"mysql"/"sqlite") |
| `encrypted_connection_string` | String | not null (Fernet ciphertext; never returned by API) |
| `created_at` | DateTime(tz=True) | default `now(utc)` |

Relationship: `user` (N→1).

### 6.2 Cardinality summary

`User 1—N Conversation 1—N Message`; `User 1—N DatabaseConnection`. Deleting a user cascades to conversations→messages and to connections (ORM cascade + FK `ON DELETE CASCADE`).

### 6.3 Migrations & engine selection

- **No migration framework** (no Alembic). Schema is created by `Base.metadata.create_all(bind=engine)` in `main.py` at startup. Schema changes to existing DBs are not managed.
- **Engine selection** (`auth/database.py`): purely from `DATABASE_URL`. `postgres://` → `postgresql://` normalized. `check_same_thread=False` applied only for `sqlite://` URLs. Default `sqlite:///./contextiq.db`.

### 6.4 Non-relational persisted state (on disk, under `backend/data/`)

Directory scheme, per user id:

- `data/raw/{user_id}/{original_filename}` — raw uploaded files (one dir per user).
- `data/vector_index/{user_id}/` — FAISS index directory. Written by `FAISS.save_local()` (produces `index.faiss` + `index.pkl`), plus:
  - `data/vector_index/{user_id}/chunks.pkl` — pickled list of LangChain `Document` chunks (backs BM25 rebuild + delete/rebuild), filename constant `CHUNKS_FILENAME = "chunks.pkl"`.
- `.gitkeep` files preserve `data/raw/` and `data/vector_index/`; contents are gitignored.
- Observed locally: `raw/{1,9001}`, `vector_index/{1,3,9001}` (user 3 index is orphaned — §1.5).
- No cache directory beyond the in-process schema cache (`sql_chain._schema_cache`, TTL 60s, keyed by `connection_id`) and the in-process embeddings singleton.

> FAISS is loaded with `allow_dangerous_deserialization=True` (`vector_store.py`) — the index pickle is trusted app-generated data. `chunks.pkl` is likewise `pickle.load`ed.

---

## 7. AUTH & SECURITY

### 7.1 Registration flow

1. `POST /api/auth/register` (rate-limited `5/15minutes`/IP).
2. `RegisterRequest` validates `email` (`EmailStr`) and `password` (strength validator → `422` on failure).
3. `register_user` (`auth_handler.py`): rejects duplicate email (`ValueError` → `400`); hashes password (bcrypt); inserts `User`.
4. Returns `UserResponse` (no password fields). **No email verification, no token issued on register** — the frontend immediately calls login (see §9.3).

### 7.2 Login flow

1. `POST /api/auth/login` (rate-limited `5/15minutes`/IP).
2. `authenticate_user`: fetch user by email; `verify_password`; returns `None` on mismatch → `401` "Incorrect email or password".
3. On success: `create_access_token({"sub": str(user.id)})` → `TokenResponse`.

### 7.3 Token creation & verification

- **Creation** (`jwt_handler.create_access_token`): `jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)`. Claims: `sub` (stringified user id) + `exp` (`now(utc) + ACCESS_TOKEN_EXPIRE_MINUTES`, default 60 min). Algorithm `HS256` (default). No refresh tokens.
- **Verification** (`jwt_handler.decode_access_token` → raises `ValueError` on `JWTError`), enforced by `api/dependencies.get_current_user`: extracts bearer via `HTTPBearer`, decodes, reads `sub`, loads `User` by id; any failure → `401` "Could not validate credentials" with `WWW-Authenticate: Bearer`.

### 7.4 Password hashing

`passlib` `CryptContext(schemes=["bcrypt"], deprecated="auto")`. bcrypt cost/params not overridden → passlib default (cost factor 12). `bcrypt` pinned `<4.1` for passlib 1.7.4 compatibility.

### 7.5 Password policy (enforced in `auth/schemas.py::_password_requirement_failures`)

- ≥ **12** characters (`PASSWORD_MIN_LENGTH = 12`).
- ≥ 1 uppercase `[A-Z]`.
- ≥ 1 lowercase `[a-z]`.
- ≥ 1 digit `\d`.
- ≥ 1 special char from `!@#$%^&*()_+-=` (`_SPECIAL_CHAR_RE = [!@#$%^&*()_+\-=]`).

Enforced server-side (source of truth); mirrored client-side in `PasswordStrengthMeter.jsx` (`PASSWORD_RULES`, gates submit — defense in depth only).

### 7.6 Per-user data isolation

- **Retrieval isolation:** each user has separate FAISS + BM25 indexes keyed by `user_id` on disk (`data/vector_index/{user_id}/`). Retrieval never crosses users because a different index is loaded (`vector_store._index_path`, `keyword_store._chunks_path`). `metadata_filter.py` only narrows *within* a user's own docs.
- **Conversation ownership:** `api/dependencies.get_owned_conversation_by_id` — `filter(Conversation.id==id, Conversation.user_id==user_id)`; missing OR foreign → `404` (indistinguishable, no existence leak). Used by every `/{conversation_id}` route + `/chat/ask`.
- **Connection ownership:** `get_owned_connection_by_id` — same pattern, `404` on missing/foreign. Used by every `/{connection_id}` route.
- **Document ownership:** documents are keyed by `data/raw/{current_user.id}/` path — a user can only list/delete/upload within their own directory.

### 7.7 Rate limiting

- Library: `slowapi` (`utils/rate_limit.py`), keyed by `get_remote_address` (client IP), `headers_enabled=False`.
- Limits: `@limiter.limit("5/15minutes")` on **both** `/api/auth/register` and `/api/auth/login`. No other route is rate-limited.
- `429` handler returns `{"detail": "Too many attempts. Please try again later. (limit: …)"}` (matches app-wide error shape).

### 7.8 Encryption at rest

- **What:** external DB connection strings (`DatabaseConnection.encrypted_connection_string`).
- **How:** Fernet (AES-128-CBC + HMAC) via `cryptography` (`utils/crypto.py`).
- **Key source:** `DB_ENCRYPTION_KEY` env var (must be a valid Fernet key). Unset → `RuntimeError` when used. Rotating it renders existing ciphertexts undecryptable (`decrypt` raises `ValueError` on `InvalidToken`).
- Decrypted strings are never logged or returned by any response schema (`ConnectionSummary` excludes them).

### 7.9 Text-to-SQL injection / write guards (defense in depth, `chain/sql_chain.py`)

1. **Text validation** (`validate_sql`): strips `/* */` and `--` comments; must start with `SELECT`; rejects trailing-`;`-plus-more (stacked queries); rejects a large forbidden-keyword set: `INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, REVOKE, EXEC, EXECUTE, ATTACH, DETACH, PRAGMA, CREATE, REPLACE, MERGE, CALL, VACUUM, REINDEX, COPY, OUTFILE, DUMPFILE, LOAD_FILE`. Detects an existing `LIMIT`. Errors tagged with `layer` (`empty_statement`/`select_only`/`stacked_query`/`forbidden_keyword`).
2. **Read-only connection** (`_readonly_connection`): sqlite → OS-level `file:...?mode=ro&uri=true`; postgres → `postgresql_readonly=True` (server-enforced); mysql → `SET SESSION TRANSACTION READ ONLY`.
3. **Statement timeout** (default 10s): postgres `SET statement_timeout`; mysql `SET SESSION MAX_EXECUTION_TIME`; sqlite `set_progress_handler` abort. (Documented gap: **MariaDB** ignores `MAX_EXECUTION_TIME` → no server-enforced timeout there.)
4. **Row cap** (default 200): fetches `row_limit+1` to detect truncation; displayed SQL always shows `LIMIT {row_limit}`.
5. **Prompt-level guard** (`SQL_PROMPT_TEMPLATE`): instructs SELECT-only; on modification requests, emit `SELECT 1 WHERE 1=0`.
6. Values serialized safely (`datetime/date`→iso, `Decimal`→float, bytes→utf-8 replace).

### 7.10 Honest list of security gaps / observations

- `.env.example` ships **real-looking committed secrets** (`SECRET_KEY`, `DB_ENCRYPTION_KEY`, `GROQ_API_KEY`) — should be rotated & replaced with placeholders (§3.2, §14).
- `SECRET_KEY` default is an insecure literal (`"insecure-dev-secret-change-me"`) if the env var is unset.
- No token revocation / refresh / logout-server-side; JWT valid until `exp`.
- Client stores token+user in `localStorage` (XSS-exposed; deliberate trade-off, see `api.js` comment).
- CORS allows a **single** origin (`FRONTEND_ORIGIN`); no multi-origin support.
- FAISS + BM25 indexes are `pickle`-deserialized with `allow_dangerous_deserialization=True` — safe only because they're app-generated (trust the disk).
- Text-to-SQL validation is regex-level, not a real SQL parser (a keyword/`;` inside a string literal could evade text checks) — mitigated by the read-only connection layer, explicitly documented in code.
- MariaDB statement-timeout gap (§7.9).
- No per-request body-size limit / upload-size cap observed on `/documents/upload`.
- Upload uses `file.filename` directly in `os.path.join` for the raw path (no explicit path-traversal sanitization observed on `filename`).

---

## 8. CORE PIPELINES

### 8.1 Document ingestion

Entry: `POST /api/documents/upload` → `documents_routes.upload_document`.

1. `is_supported_file` (ext ∈ `{.pdf,.docx,.txt,.csv,.md}`).
2. Save to `data/raw/{user_id}/{filename}`.
3. `load_document(file_path)` (`loaders/document_loader.py`) dispatch by extension:
   - `.pdf` → `load_pdf_with_scan_detection` — `PyPDFLoader` (1 Document/page); if `is_likely_scanned_pdf` (≥80% of pages have <20 non-ws chars) → raises `ScannedPDFError` (→ `422`, file kept but not indexed). No OCR.
   - `.docx` → `load_docx_by_section` — one Document per heading-delimited section (`python-docx`; heading styles matched by `^(heading\s*\d+|title)$`); tags `section_heading` metadata; text before first heading → `section_heading=None`.
   - `.md` → `load_md_by_section` — one Document per ATX-heading section (`^#{1,6}\s+…`); fenced code (```` ``` ```` / `~~~`) never treated as headings; setext headings not supported.
   - `.txt` → `TextLoader`; `.csv` → `CSVLoader` (from `LOADER_MAP`).
4. `chunk_documents` (`ingestion/chunking.py`): `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)`; each chunk tagged `{user_id, file_name, file_type}` (+ inherited `section_heading` for DOCX/MD).
5. **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (`ingestion/embeddings.py`), process-wide cached `HuggingFaceEmbeddings` singleton.
6. `build_faiss_index` (`ingestion/vector_store.py`): if index dir exists, `FAISS.load_local(..., allow_dangerous_deserialization=True).add_documents`; else `FAISS.from_documents`; `save_local`.
7. `save_chunks` (`ingestion/keyword_store.py`): appends chunks to `chunks.pkl`.

Delete path: `remove_chunks_for_file` (drop file's chunks from `chunks.pkl`) → `rebuild_faiss_index` (re-embed all remaining chunks from scratch; if none, `rmtree` the index dir). O(total remaining chunks) per delete — documented trade-off (no FAISS delete-by-metadata).

> Frontend serializes uploads one-at-a-time (`Documents.jsx` `chainRef`) to avoid concurrent per-user FAISS rebuilds racing/corrupting the single index file (no server-side locking).

### 8.2 Retrieval + answering (`chain/rag_chain.py::run_rag_chain`)

1. `rewrite_query(question, history)` — if history, LLM rewrite to standalone query (see §8.6); else unchanged.
2. `get_hybrid_retriever(user_id)` (`chain/hybrid_retriever.py`): `EnsembleRetriever([FAISS, BM25], weights=[0.5, 0.5])`; each sub-retriever `k = TOP_K_PER_RETRIEVER = 8`. Returns `None` if user has no index → canned "upload a document" answer.
3. `retriever.invoke(rewritten_query)[:FETCH_K]` — **`FETCH_K = 8`**.
4. `filter_documents(candidates, file_type, file_name)` — post-retrieval metadata filter.
5. `relevant_chunks = filtered[:TOP_K]` — **`TOP_K = 4`**. If empty → "I couldn't find anything relevant…".
6. Context assembled: each chunk prefixed `[Source: <file> | Section: <heading>]` (`_format_chunk_header`; Section only when present).
7. Prompt selection (`_select_prompt_template`): if all retrieved chunks share one `file_type` → `PROMPT_REGISTRY[type]`; else `DEFAULT_PROMPT_TEMPLATE`.
8. Prompt formatted with `history` (rendered or `(none)`), `context`, `question` (the **original**, not rewritten).
9. **LLM:** `ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL_NAME, temperature=0)` — default model `llama-3.1-8b-instant`.
10. `sources` = sorted unique `file_name`s of the used chunks.
11. Returns `{answer, sources, rewritten_query}`.

### 8.3 Computational path — CSV (`chain/csv_compute.py`)

Routed when `file_type=="csv"` **and** `csv_query_classifier.is_computational_question(question)` (regex for average/mean/median, total/sum, count/how many/number of, top N, bottom N, highest/max, lowest/min, group by).

1. `resolve_target_csv_file` — explicit `file_name` (must be `.csv`), else the sole CSV if exactly one; else `None`→ fall back to RAG.
2. `load_csv_dataframe` — `pd.read_csv(keep_default_na=False, na_values=[""])` (so "NA"/"NULL"/"None" data values aren't dropped).
3. `build_compute_plan` — regex operation detection (priority: top_n → bottom_n → max → min → mean → median → sum → count); column resolution from **real DataFrame column names only** (`_find_named_column`, `_find_group_by_column` via "by "/"per "); single numeric column auto-selected; returns `None` (→ RAG) if unresolvable. Ops ∈ `{sum,mean,median,count,max,min,top_n,bottom_n}`.
4. `execute_plan` — fixed dispatch over pandas (`.sum/.mean/.median/.max/.min/.count/.groupby/.sort_values.head`). **No eval/exec/query; no user text reaches pandas** — closed op set + validated column names only.
5. `format_result_as_fact` → plain-English fact stating it was computed over the full file.
6. `_phrase_result` — `ChatGroq(temperature=0)` phrases the fact only (told not to recompute).
7. Returns `{answer, sources:[file], rewritten_query:None}` or `None` (fall back).

### 8.4 Full-document path — DOCX/PDF/MD (`chain/{docx,pdf,md}_compute.py`)

Routed when `file_type ∈ {docx,pdf,md}` and the matching classifier fires (`FULL_DOCUMENT_HANDLERS` in `chat_routes.py`). Each mirrors the CSV compute-first shape.

- **Resolve file** (`resolve_target_*`): explicit `file_name` or the sole file of that type.
- **Operations** (`ALLOWED_OPERATIONS`):
  - DOCX: `word_count, page_count, heading_list, table_list, summarize, extract_all`.
  - PDF: same six.
  - MD: `word_count, heading_list, summarize, extract_all` (no page/table — MD has no pages, tables are inline text).
- **Structural facts** computed directly, LLM only phrases (`COMPUTE_PHRASING_PROMPT`):
  - DOCX word count includes table-cell words; **page count is deliberately refused** (docx has no authoritative page count → returns word count instead).
  - PDF page count is **reliable** (from page tree); word count over extracted text; headings from embedded outline (`PdfReader.outline`, honestly reports "no outline"); **table extraction not supported** (honest non-answer; pypdf can't); scanned PDFs short-circuit to an honest answer.
  - MD headings from `load_md_by_section`.
- **Summarize / extract_all** need the LLM over full text, **capped at `MAX_DOCUMENT_CHARS = 24_000`** (~6k tokens); over cap → explicit refusal (`_too_large_answer`) instead of silent truncation. Prompts: `SUMMARIZE_PROMPT`, `EXTRACT_ALL_PROMPT`.
- Returns `{answer, sources:[file], rewritten_query:None}` or `None` (fall back to RAG).

### 8.5 Text-to-SQL pipeline (`chain/sql_chain.py::run_sql_chain`)

Entry: `POST /api/databases/{connection_id}/ask` (ownership-verified connection).

1. `decrypt_connection_string` (Fernet).
2. `get_schema_snapshot` — `inspect(engine)`; `{table: [(col_name, str(col_type))…]}`; cached per `connection_id` for `SCHEMA_CACHE_TTL_SECONDS=60`.
3. `format_schema_for_prompt` → `table(col type, …)` lines.
4. `generate_sql` — `ChatGroq(temperature=0)` with `SQL_PROMPT_TEMPLATE`; `_extract_sql` strips ``` ```sql ``` fences.
5. `validate_sql` (§7.9) → `(cleaned_sql, has_own_limit)`.
6. `execute_query` — read-only connection + statement timeout; fetch `row_limit+1` (200 default) when no own LIMIT; serialize values; returns `(columns, rows, row_count, truncated, displayed_sql)`.
7. `summarize_answer` — `ChatGroq(temperature=0)` with `SQL_ANSWER_PROMPT_TEMPLATE` over up to `ANSWER_ROW_CONTEXT_LIMIT=50` rows.
8. Returns dict → `DBQueryResponse`.

Each stage wrapped/logged separately (`logger.exception`/`logger.warning`); `OperationalError` classified into `SQLExecutionTimeout` (504) / `SQLConnectionError` (503, MySQL errnos `2003/2006/2013/4031` + message markers) / passthrough (502). `test_connection` (used on create) does a real connect + `SELECT 1` with a 5s connect timeout.

### 8.6 Conversation history

- **Storage:** `messages` table (role/content/sources), ordered by `created_at`.
- **Retrieval into prompt:** `chat_routes._recent_history` takes the last `DEFAULT_HISTORY_TURNS*2 = 6` messages (3 user/assistant pairs) as `[{role,content}]`.
- **Use:** (a) `rewrite_query` turns follow-ups into standalone queries for retrieval; (b) the answering prompt receives `format_history(history)` so the model has prior context; the **original** question is what's answered. `rewritten_query` is returned on the live response but **not persisted** (frontend shows it only for the current session).

### 8.7 Prompt templates (full inventory)

All are `langchain_core.prompts.PromptTemplate`. `PROMPT_REGISTRY` (`prompt_eng/__init__.py`) keys: `csv, pdf, docx, txt, md, sql`.

- **`base_prompt.py`** — `BASE_INSTRUCTIONS` ("You are ContextIQ … answer strictly using the given context … cite file(s) with 'Source:' … use prior conversation only to resolve references"); `ANSWER_SECTION` (`Prior conversation:{history}\n\nContext:{context}\n\nQuestion:{question}\n\nAnswer:`); `DEFAULT_PROMPT_TEMPLATE` = BASE + ANSWER.
- **`csv_prompt.py`** — `CSV_GUIDANCE` (schema awareness, per-row reasoning, aggregation caveats: never present a computed aggregate over a partial sample as exact) → `CSV_PROMPT_TEMPLATE`.
- **`docx_prompt.py`** — `DOCX_GUIDANCE` (section awareness, structure preservation, scope honesty) → `DOCX_PROMPT_TEMPLATE`.
- **`md_prompt.py`** — `MD_GUIDANCE` (header hierarchy, preserve code/lists, scope honesty) → `MD_PROMPT_TEMPLATE`.
- **`pdf_prompt.py`** — `PDF_GUIDANCE` (extraction noise, page-number citation only if visible, document-type awareness, scope honesty) → `PDF_PROMPT_TEMPLATE`.
- **`txt_prompt.py`** — `TXT_GUIDANCE` (rely on surrounding sentences; scope honesty) → `TXT_PROMPT_TEMPLATE`.
- **`sql_prompt.py`** — `SQL_PROMPT_TEMPLATE` (NL→one SELECT; SELECT-only, `SELECT 1 WHERE 1=0` on modification asks; schema-only tables/columns; no markdown) and `SQL_ANSWER_PROMPT_TEMPLATE` (summarize result rows in plain language). Only `SQL_PROMPT_TEMPLATE` is in the registry; the answer prompt is imported by name.
- **Compute-path prompts** (not in registry): each compute module has its own `COMPUTE_PHRASING_PROMPT`, plus `SUMMARIZE_PROMPT`/`EXTRACT_ALL_PROMPT` (DOCX/PDF/MD) and `COMPUTE_PHRASING_PROMPT` (CSV). `query_rewriter.REWRITE_PROMPT` handles follow-up rewriting.

(Full template text is in the named files; exact strings quoted in §8 above and the source.)

---

## 9. FRONTEND

### 9.1 Routing table (`src/App.jsx`)

| Path | Component | File | Gate |
|---|---|---|---|
| `/` | Landing | `pages/Landing.jsx` | `PublicOnlyRoute` (authed → `/app`) |
| `/login` | Login | `pages/Login.jsx` | `PublicOnlyRoute` |
| `/register` | Register | `pages/Register.jsx` | `PublicOnlyRoute` |
| `/product` | Product | `pages/marketing/Product.jsx` | none (public content) |
| `/databases` | DatabasesInfo | `pages/marketing/Databases.jsx` | none |
| `/docs` | Docs | `pages/marketing/Docs.jsx` | none |
| `/app` | AppLayout | `components/AppLayout.jsx` | `ProtectedRoute` |
| `/app` (index) | → redirect `chat` | — | — |
| `/app/chat` | Chat | `pages/Chat.jsx` | protected |
| `/app/chat/:conversationId` | Chat | `pages/Chat.jsx` | protected |
| `/app/documents` | Documents | `pages/Documents.jsx` | protected |
| `/app/databases` | Databases | `pages/Databases.jsx` | protected |
| `/app/databases/:connectionId` | DatabaseQuery | `pages/DatabaseQuery.jsx` | protected |
| `*` | → redirect `/` | — | — |

### 9.2 Component inventory (key props)

Pages: **Chat** (uses `useParams`, `useAppData`; local filter by `file_type`), **Documents** (dropzone + serialized upload queue), **Databases** (add-connection form: `name`/`db_type`/`connection_string`), **DatabaseQuery** (session-only history), **Login/Register**, marketing **Product/Databases/Docs**, **Landing**.

Reusable components (props):
- `Button({variant∈{primary,secondary,ghost,danger,invert}, loading, disabled, type, className, children})`.
- `TextInput` / `PasswordInput` / `Select` (`{label, error, hint, labelClassName, ...}`; PasswordInput adds show/hide).
- `PasswordStrengthMeter({password})` + `isPasswordValid()`.
- `Dropzone({inputRef, onFiles, disabled})`.
- `ConfirmDialog({open, title, description, confirmLabel, danger, onConfirm, onCancel, loading})`.
- `Composer({onSend, disabled, activeFilter, onClearFilter, placeholder})`.
- `MessageBubble({message, onSourceClick})`; `SourceChip({source, onClick})`; `TypingIndicator`.
- `DatabaseAnswer({result})`; `ResultsTable({columns, rows})`; `CodeBlock({code})` (copy button).
- `Markdown({children})` (react-markdown+gfm); `EmptyState({icon,title,body,action})`; `FullPageSpinner`.
- `Sidebar({onNavigate})`; `AppLayout` (mobile drawer + `<Outlet/>`).
- `ThemeToggle`, `Logo({size,className})`, `AuroraBackground`, `PipelineDiagram`, `ToastViewport({toasts,onDismiss})`.
- Landing subcomponents: `AuthBrand`, `BrainMark` (exports `BRAIN_LINE_PATHS`/`BRAIN_OUTER_PATH`), `ChatMockup`, `PublicNav({active})`, `PublicFooter`, `StepList`.
- Route gates: `ProtectedRoute`, `PublicOnlyRoute`.

### 9.3 State management & where auth lives

- **React Context**, no Redux. Providers (in `main.jsx`, outer→inner): `MotionConfig` → `BrowserRouter` → `ThemeProvider` → `AuthProvider` → `ToastProvider` → `App`. `AppDataProvider` wraps only the authed shell (`AppLayout`).
- **Auth/session** (`AuthContext`): `token` + `user` in state; persisted to `localStorage` (`contextiq.token`, `contextiq.user`). On mount, restores token, decodes JWT, checks `exp` (client-side) before treating as signed in. `login` calls `/login` then derives `{id:sub, email}` (login returns no user object); `register` calls `/register` then immediately `/login`. `logout` clears both.
- **App data** (`AppDataContext`): `conversations`, `documents`, `databaseConnections` (+ loading/error + `refresh*`), fetched on mount — one source of truth for sidebar counts/lists.
- **Theme** (`ThemeContext`): `light`/`dark`, persisted `contextiq.theme`, defaults to OS `prefers-color-scheme`, toggles `.dark` on `<html>`.
- **Toasts** (`ToastContext`): additive queue (`success`/`error`/`show`), auto-dismiss default 4000ms.

### 9.4 API client (`src/services/api.js`)

- `axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000" })`.
- **Token attach:** request interceptor adds `Authorization: Bearer <token>` from `localStorage["contextiq.token"]`.
- **Error handling:** response interceptor — a `401` from any non-auth endpoint clears the token and hard-redirects to `/login`; `401` from `/login`/`/register` is left as-is (it's just "wrong password"). `getErrorMessage()` normalizes both `{detail:string}` and Pydantic `{detail:[{msg}]}` shapes.
- Exposes wrappers for every endpoint (register, login, list/upload/delete documents, conversations CRUD, `askQuestion`, DB connections CRUD, `askDatabaseQuestion`, `checkHealth`). Token helpers: `getToken/setToken/clearToken`.

### 9.5 Design system (as implemented)

- **Tokens** (`index.css`, CSS variables as RGB triplets; `.dark` overrides). Light: `--color-bg 250 250 250`, `--color-surface 255 255 255`, `--color-surface-hover 244 244 245`, `--color-border 228 228 231`, `--color-foreground 24 24 27`, `--color-muted 113 113 122`, `--color-accent 79 70 229` (indigo), `--color-accent-foreground 255 255 255`, `--color-danger 220 38 38`, `--color-danger-foreground 255 255 255`, `--color-success 22 163 74`, `--color-aurora-violet 168 85 247`, `--color-aurora-cyan 34 211 238`, pipeline surface/border/label `238 237 254 / 127 119 221 / 60 52 137`.
- **Dark:** `bg 9 9 11`, `surface 24 24 27`, `surface-hover 39 39 42`, `border 39 39 42`, `foreground 244 244 245`, `muted 161 161 170`, `accent 129 140 248`, `accent-foreground 9 9 11`, `danger 248 113 113`, `success 74 222 128`, aurora `192 132 252` / `103 232 249`, pipeline `34 30 58 / 148 140 240 / 199 195 255`.
- **Typography** (`tailwind.config.js`, scales **replaced** not extended): `xs 12/16, sm 13/18, base 14/20, md 16/24, lg 20/28, xl 24/32` + marketing-only `2xs 11.5, display-xs 30, display-sm 32, display-md 44`. Weights: `normal 400, medium 500` (+ marketing `semibold 600, bold 700`). Font stack: `-apple-system, BlinkMacSystemFont, Inter, Segoe UI, Helvetica Neue, Arial, sans-serif`.
- **Radius:** `md 6px, lg 8px, xl 12px, 2xl 18px`. **Shadows:** `glass`, `glass-lg`, `glow`. **Backdrop blur:** `xs 2px`.
- **Animations:** `aurora-drift` (18s) / `-slow` (26s reverse), `shimmer` (2s), pipeline `flow/hub/ripple/line-in/pill-in/card-in`. Reduced-motion handled via `<MotionConfig reducedMotion="user">` and `@media (prefers-reduced-motion)` in CSS.
- **Component classes** (CSS): `.glass-panel`, `.aurora-orb`, `.skeleton`, `.markdown-body` (+ children), focus-visible ring `2px accent`.

---

## 10. TESTING

- **Framework:** `pytest` (8.4.2). Run: `pytest backend/tests/ -v` (from repo root, per README) or `python3 -m pytest tests/` from `backend/`. No pytest config file beyond `.pytest_cache`. `asyncio` plugin present but tests are sync.
- **Verified run (this audit):** `58 passed in 17.15s` under Python 3.13.9. Full pass, zero failures/skips.

| Test file | Test defs | Runtime cases | Area |
|---|---|---|---|
| `test_auth.py` | 4 | 4 | Register success, duplicate-email `400`, login success, wrong-password `401`. |
| `test_auth_security.py` | 7 | 7 | Password rules (short/upper/digit/special/valid), register + login rate-limit `429` after 5. |
| `test_csv_compute.py` | 5 | 5 | Average, top-N, non-computational fallback, region-named-"NA" not dropped, multi-CSV-no-filename fallback. |
| `test_document_loader_pdf.py` | 7 | 7 | Scanned-PDF detection heuristics + clear error + routing + normal PDF load. |
| `test_docx_compute.py` | 5 | 5 | Full-doc summary, exhaustive extraction, non-full-doc fallback, computed word count, too-large refusal. |
| `test_md_compute.py` | 6 | 6 | Header hierarchy metadata, fenced-code-`#` not heading, summary, fallback, computed heading list, too-large refusal. |
| `test_pdf_compute.py` | 8 | 8 | Summary, extraction, fallback, exact page count, outline present/absent, too-large refusal, scanned short-circuit. |
| `test_sql_chain.py` | 11 | 20 (parametrized) | `OperationalError` classification: MySQL errno/message connection-lost, mysql-only, per-db timeout, timeout≠conn-lost, unrecognized passthrough, `execute_query` wiring. |

**Total: 58 runtime cases.**

**Untested areas (no tests found):**
- Chat routing (`/chat/ask`) end-to-end, conversation CRUD routes, document upload/list/delete routes, databases routes (`create/list/delete/ask`).
- `rag_chain.run_rag_chain`, `hybrid_retriever`, `metadata_filter`, `query_rewriter`, `ingestion/*` (chunking/embeddings/vector_store/keyword_store), `utils/crypto`, `sql_chain` happy path (only error classification is tested — no validate_sql / execute path over a real DB / summarize tests).
- Entire frontend (no test runner configured; no `*.test.*`/`*.spec.*` files).
- Ownership/isolation dependencies (`get_owned_conversation`, `get_owned_connection`) not directly unit-tested.

---

## 11. EVALUATION

- **Location:** `eval/`. Measures **retrieval quality** (not answer quality) across three configs: FAISS-only, BM25-only, Ensemble (Hybrid) — all via the app's real functions (read-only w.r.t. app code).
- **Metrics:** Precision@K, Recall@K, MRR, MAP, latency p50/p95, plus Recall@K by category (`exact_number`, `rare_term`). K = `TOP_K = 4` (`config.py`). Standard IR definitions implemented in `run_eval.py`.
- **Methodology:** synthetic 10-document / ~17-chunk corpus (2 docs per file type) ingested into eval user `9001` via the real pipeline (`build_eval_corpus.py`); 28 labeled questions with ground-truth `relevant_chunk_ids` (`eval_set.json`, all `verified:true`). Latency includes retriever construction (indexes rebuilt per call, no caching); one untimed warm-up per config. Chunk ids reconstructed as `<file>::<index>` from `chunks.pkl` order.
- **Recorded results (`eval/results.md`, generated 2026-08-07, 28 q, 17 chunks, K=4):**

| Metric | FAISS-only | BM25-only | Ensemble (Hybrid) |
|---|---|---|---|
| Precision@K | 25.0% | 22.3% | 25.0% |
| Recall@K | 100.0% | 89.3% | 100.0% |
| MRR | 0.964 | 0.869 | 0.893 |
| MAP | 0.964 | 0.869 | 0.893 |
| Latency p50 (ms) | 12.2 | 0.7 | 12.4 |
| Latency p95 (ms) | 44.6 | 0.8 | 13.6 |

Recall by category — exact_number: 100.0 / 87.5 / 100.0; rare_term: 100.0 / 91.7 / 100.0 (FAISS / BM25 / Hybrid). Key finding: **BM25-only misses 3 exact-value questions (q04, q14, q15) that Hybrid recovers** (+12.0% recall vs BM25).
- **Weight sweep (`weight_tuning_summary.md`, K=4):** 0.5/0.5, 0.6/0.4, 0.7/0.3, 0.8/0.2 — Precision/Recall identical (25.0%/100.0%); MRR/MAP move +0.006 once FAISS≥0.6 (one question, q04, re-ranks 3→2). Recommendation: **keep 0.5/0.5** (default unchanged in `hybrid_retriever.py`); a one-question effect on a 17-chunk corpus isn't a generalizable signal.
- **Caveat (from `eval_set.json._meta.READ_ME_BEFORE_CITING`):** tiny synthetic corpus — illustrative of hybrid-vs-single behavior, not a production-scale benchmark. Note `_meta.top_k` says 5 but the actual harness uses `TOP_K=4` (config.py) — the results were generated at K=4.

---

## 12. GIT & PROJECT HISTORY

- **Current branch:** `main`. **Working tree:** NOT clean — 27 modified tracked files and 21 untracked new paths (Docker files, `docker-compose.yml`, rate limiter, security tests, SQL-chain test, marketing pages, landing components, toast/aurora/pipeline components, `motion.js`). None committed yet.
- **Commit log (oldest → newest):**
  1. `afa0d94` — 2026-08-05 — `first commit`
  2. `f4d5b34` — 2026-08-08 — `Add hybrid retrieval evaluation, per-file-type prompts, computational query paths, and project documentation`
- **`.gitignore` contents:** Python (`__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `*.egg-info/`, `.pytest_cache/`); env (`.env`, `.env.local`, `.env.*.local`); secrets (`*.pem`, `*.key`); databases (`*.db`, `*.sqlite3`); logs (`*.log`); data (`backend/data/raw/*` + `!.gitkeep`, `backend/data/vector_index/*` + `!.gitkeep`); node/frontend (`node_modules/`, `dist/`, `frontend/.env`); editor/OS (`.vscode/`, `.idea/`, `.DS_Store`); and `.claude/` (Claude Code tooling).

---

## 13. RUNNING THE PROJECT

### 13.1 Local (non-Docker), per README

Backend:
```bash
cd ContextIQ/backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env      # then set SECRET_KEY, DB_ENCRYPTION_KEY, GROQ_API_KEY
uvicorn main:app --reload    # http://localhost:8000 (docs at /docs)
```
Frontend:
```bash
cd ContextIQ/frontend
npm install
cp .env.example .env         # VITE_API_BASE_URL defaults to http://localhost:8000
npm run dev                   # http://localhost:5173
```
Tests: `pytest backend/tests/ -v`.

### 13.2 Docker

`cp .env.example .env` (fill secrets) → `docker-compose up --build`. Backend published on host `8000`, frontend on host `5173` (nginx :80 inside). Backend `DATABASE_URL` overridden to `sqlite:////app/data/contextiq.db` (inside `backend_data` volume) unless `DOCKER_DATABASE_URL` set. `VITE_API_BASE_URL` is a build ARG (must be browser-reachable). Healthchecks on both; frontend `depends_on` backend healthy.

### 13.3 Required services & versions

- **Groq API** — required (LLM inference), free key.
- **Embedding model** — `sentence-transformers/all-MiniLM-L6-v2` (downloaded on first use locally; pre-baked in the backend image).
- **App DB** — SQLite default (no external service); optionally Postgres (psycopg2) / MySQL (PyMySQL) via `DATABASE_URL`.
- **External SQL DBs** — only for the text-to-SQL feature, user-provided per connection (Postgres/MySQL/SQLite).
- Python 3.11+ (image 3.11), Node 18+ (build image 20).

### 13.4 Seed/setup

No DB seeding required (tables auto-created at startup). Only env config + (for eval) `build_eval_corpus.py`. First upload/question locally triggers a one-time embedding-model download.

### 13.5 Ports

- Backend API: **8000**. Frontend dev: **5173**. Docker frontend host: **5173** → nginx **80**. External DB ports are per user-supplied connection string.

---

## 14. CURRENT STATE & GAPS

### 14.1 Fully working (verified by reading code + passing tests)

- Auth: register (strength-validated), login (JWT), rate limiting, password hashing — all covered by passing tests.
- Per-file-type compute paths (CSV aggregation; DOCX/PDF/MD structural + summarize/extract with size cap and honest refusals; scanned-PDF detection) — covered by passing tests.
- Text-to-SQL error classification (timeout vs connection-lost vs passthrough) — covered by passing tests.
- RAG pipeline, hybrid retrieval, ingestion, ownership isolation, conversations/documents/databases routes — present and internally consistent (not directly unit-tested; §10).
- Docker build/run stack + eval harness (with recorded results).

### 14.2 Incomplete / stubbed / documented gaps

- **OCR:** not implemented; scanned PDFs rejected at upload with an actionable error (needs system `tesseract` + `pytesseract` + `PyMuPDF`). Documented in `document_loader.py` and README.
- **PDF table extraction:** not supported (`pdf_compute.format_structural_fact` returns an honest non-answer; would need pdfplumber/camelot).
- **DOCX page count:** deliberately not reported (no authoritative value) — returns word count instead.
- **MariaDB statement timeout:** silently ignored (`MAX_EXECUTION_TIME` unsupported) — documented in `sql_chain.py`.
- **DB query history:** not persisted server-side; `DatabaseQuery.jsx` is session-only (comment: "no backend support for persisting DB query history").
- **Conversation titles:** client-side heuristic (`lib/titles.js`) — comment notes the "correct" LLM-based version needs a new backend endpoint (not built).
- **`rewritten_query`** not persisted (only shown for live/session messages).
- **Deployment:** README "Deployment" section says "Planned (Render + Vercel), instructions coming soon" — not implemented (though Docker stack exists).
- **Stale note:** `eval/README.md`'s "Known issue" about `Docx2txtLoader`/`docx2txt` is obsolete — code now uses `python-docx`.

**TODO/FIXME grep:** no literal `TODO`/`FIXME` comments were found in backend or frontend source; gaps are documented in prose within docstrings/comments (as quoted above) rather than tagged markers.

### 14.3 Hardcoded values that would break / need attention in production

- `.env.example` ships **real-looking committed secrets** (`SECRET_KEY`, `DB_ENCRYPTION_KEY`, `GROQ_API_KEY`) — must be rotated and replaced with placeholders before any public use.
- `SECRET_KEY` insecure fallback (`"insecure-dev-secret-change-me"`) if env unset.
- CORS is a single origin from `FRONTEND_ORIGIN` (default `http://localhost:5173`).
- Default `DATABASE_URL` is a **cwd-relative** SQLite path (`sqlite:///./contextiq.db`) — behaves differently by process cwd; docker-compose explicitly overrides it to a volume path to avoid data loss on rebuild.
- Per-user FAISS index has no concurrency locking server-side (relies on the frontend serializing uploads); document delete re-embeds the whole remaining corpus (O(N)); both are documented scaling caveats.
- `VITE_API_BASE_URL` is compiled into the JS bundle at build time (no runtime override).

### 14.4 Not yet done for deployment

- No production hosting config (no Render/Vercel/Fly manifests; no CI/CD). Docker Compose exists but README deployment instructions are "coming soon".
- No HTTPS/TLS termination config beyond nginx serving static frontend.
- No logging/monitoring/observability stack, no error tracking, no metrics endpoint (only `/health` + `/healthz`).
- No secrets management beyond `.env`/env vars.
- No Alembic migrations (schema via `create_all` only) — problematic for evolving a production DB.
- No frontend test/CI, no backend integration tests for the route layer.
