# Project Tree

Documentation only — nothing here affects how the app runs. Generated dirs
(`node_modules/`, `__pycache__/`, `.pytest_cache/`, `frontend/dist/`,
`backend/data/{raw,vector_index}/*`, `.claude/`, `.git/`) are omitted; see
`.gitignore` for the full list of what's excluded from version control.

```text
ContextIQ/
├── README.md                  Project overview, setup, features, evaluation summary
├── PROJECT_TREE.md            This file
├── .env.example                Template for backend/.env (auth secrets, DB URL, Groq API key)
├── .gitignore
│
├── backend/                   FastAPI application
│   ├── main.py                 App entrypoint: wires up CORS + all routers, creates DB tables
│   ├── requirements.txt        Pinned Python dependencies
│   │
│   ├── api/                    FastAPI route handlers
│   │   ├── chat_routes.py        /api/chat/ask — routes each question to the right path:
│   │   │                         computational (CSV) or full-document (DOCX/PDF/MD) when a
│   │   │                         classifier flags it, else the normal RAG chain
│   │   ├── documents_routes.py   Upload/list/delete documents; surfaces scanned-PDF errors
│   │   ├── auth_routes.py        Register / login (JWT)
│   │   ├── conversations_routes.py, databases_routes.py, dependencies.py
│   │   └── __init__.py
│   │
│   ├── auth/                   User accounts, JWT auth, and SQLAlchemy models
│   │                           (users, conversations/messages, saved DB connections)
│   │
│   ├── chain/                  RAG orchestration, retrieval, and the per-file-type
│   │   │                       computational/full-document paths
│   │   ├── rag_chain.py          Core RAG pipeline: rewrite query → retrieve → filter →
│   │   │                         prompt → generate; the default path for every question
│   │   ├── hybrid_retriever.py   Builds the FAISS + BM25 EnsembleRetriever (hybrid search)
│   │   ├── query_rewriter.py     Rewrites conversational follow-ups into standalone queries
│   │   ├── metadata_filter.py    Post-retrieval filtering by file_type / file_name
│   │   ├── sql_chain.py          Text-to-SQL: natural language → SQL against a connected
│   │   │                         external Postgres/MySQL database
│   │   ├── csv_compute.py + csv_query_classifier.py     Exact pandas aggregation
│   │   │                         (sum/mean/count/min/max/top-N/group-by) over full CSVs,
│   │   │                         bypassing retrieval for questions that need it
│   │   ├── docx_compute.py + docx_query_classifier.py   Full-document DOCX path: word
│   │   │                         count, heading list, table extraction, whole-document
│   │   │                         summaries/exhaustive extraction
│   │   ├── pdf_compute.py + pdf_query_classifier.py     Same, for PDF (page count via the
│   │   │                         PDF's real page tree, outline/table-of-contents if present)
│   │   └── md_compute.py + md_query_classifier.py       Same, for Markdown
│   │
│   ├── ingestion/               Chunking, embeddings, and index management
│   │   ├── chunking.py            Splits loaded documents into overlapping chunks
│   │   ├── embeddings.py          Sentence-transformers embedding model wrapper
│   │   ├── vector_store.py        FAISS index build/load/persist, per user
│   │   └── keyword_store.py       BM25 index + persisted chunk storage, per user
│   │
│   ├── loaders/
│   │   └── document_loader.py    Per-file-type loading: scanned-PDF detection (flags
│   │                             image-only PDFs instead of silently indexing them empty),
│   │                             section-aware DOCX/Markdown loading (heading metadata)
│   │
│   ├── prompt_eng/               Per-file-type prompt templates (pdf/docx/csv/txt/md/sql)
│   │                             plus shared base instructions
│   │
│   ├── utils/                    Crypto helpers (encrypting saved DB connection strings)
│   │                             and small file/type helpers
│   │
│   ├── tests/                    Pytest suite: auth, and the csv/docx/pdf/md compute paths
│   │                             (aggregation correctness, full-document summaries,
│   │                             exhaustive extraction, fallback-to-RAG behavior)
│   │
│   └── data/                     Runtime data — created on first upload, gitignored
│       ├── raw/<user_id>/          Original uploaded files, one directory per user
│       └── vector_index/<user_id>/ Per-user FAISS index + persisted BM25 chunks
│
├── frontend/                  React (Vite) single-page app
│   ├── package.json             Scripts (dev/build/preview) and dependencies
│   ├── vite.config.js, tailwind.config.js, postcss.config.js   Build/styling tooling config
│   ├── .env.example              Template for frontend/.env (backend API base URL)
│   │
│   └── src/
│       ├── main.jsx, App.jsx      App entrypoint and route definitions
│       ├── pages/                  Route-level views: Landing, Login, Register, Documents,
│       │                          Chat, Databases, DatabaseQuery
│       ├── components/             Reusable UI: chat bubbles, dropzone, sidebar, markdown
│       │                          rendering, theming, etc.
│       ├── context/                React context providers: auth, app data, theme
│       ├── lib/                    Small client-side helpers (JWT decode, file/DB-type
│       │                          constants, conversation title generation)
│       └── services/api.js         Single axios client wrapping every backend endpoint
│
└── eval/                      Retrieval evaluation harness (see eval/README.md)
    ├── eval_set.json            28 labeled questions across all 5 file types, with
    │                            ground-truth relevant chunk IDs
    ├── run_eval.py              Runs FAISS-only / BM25-only / Hybrid, computes
    │                            Precision@K, Recall@K, MRR, MAP, and p50/p95 latency
    ├── build_eval_corpus.py     One-time script that ingests eval/fixtures/ into a
    │                            dedicated eval user via the app's real ingestion pipeline
    ├── config.py                Shared constants (eval user id, K)
    ├── fixtures/                Synthetic source documents (2 per file type) used to
    │                            build the eval corpus; fixtures/source/ holds the
    │                            plaintext originals for the PDF/DOCX conversions
    └── results*.md / results*.json   Benchmark run outputs: the K=4 baseline and an
                                 ensemble-weight sensitivity sweep, plus a summary
                                 with a citable recommendation
```
