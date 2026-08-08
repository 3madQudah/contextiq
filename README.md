# ContextIQ

ContextIQ is a retrieval-augmented generation (RAG) system that lets each user upload their own documents — PDFs, Word docs, spreadsheets, text, and Markdown — and ask questions about them in natural language, with every answer grounded in and cited back to the source file. It also supports connecting an external SQL database and querying it in plain English. Retrieval is hybrid (semantic + keyword) rather than pure vector search, and for the cases where retrieval alone can't be trusted — exact CSV aggregates, whole-document summaries — ContextIQ computes or reads the complete source directly instead of guessing from a handful of chunks.

## Key features

- **Hybrid retrieval** — an `EnsembleRetriever` combining FAISS (semantic/vector) search with BM25 (keyword) search, so exact terms, IDs, and numbers that pure vector search tends to miss are still found.
- **Per-file-type prompts** — PDF, DOCX, CSV, TXT, Markdown, and SQL each get prompt guidance tailored to how that format actually behaves (e.g. handling PDF extraction noise, CSV aggregation caveats, DOCX/Markdown section structure).
- **Cited answers** — every response names the specific file(s) it was drawn from.
- **Per-user isolation** — each user has their own FAISS index, BM25 index, and document storage; nothing crosses between accounts.
- **Text-to-SQL** — connect an external Postgres or MySQL database and ask questions in plain English, translated to SQL against your actual schema.
- **Exact CSV computation** — aggregation questions ("average of column X", "top 5 by revenue", "total by region") are computed directly with pandas over the complete file, not estimated from retrieved chunks.
- **Full-document analysis for DOCX/PDF/Markdown** — structural questions (word/page count, heading list) and exhaustive ones (whole-document summaries, "list every date mentioned") are answered from the complete document text, with an explicit refusal instead of a silently partial answer if a document is too large to process in one pass.
- **Section-aware chunking** — DOCX and Markdown documents keep their heading/section structure as chunk metadata, so retrieved context tells you (and the model) which section it came from.
- **Scanned-PDF detection** — a PDF with no extractable text layer is flagged at upload time with a clear error, instead of silently indexing as empty.

## Tech stack

**Backend:** Python, FastAPI, SQLAlchemy (SQLite by default; Postgres/MySQL supported), JWT auth (python-jose, passlib, bcrypt), LangChain, FAISS (`faiss-cpu`), BM25 (`rank_bm25`), sentence-transformers, Groq (LLM inference), pandas, pypdf, python-docx

**Frontend:** React (Vite), Tailwind CSS, axios, react-router-dom, react-markdown

## Supported file types

PDF · DOCX · CSV · TXT · Markdown

## Setup

Assumes a clean machine with nothing installed yet.

### Prerequisites

- Python 3.11+
- Node.js 18+
- `git`
- A free [Groq API key](https://console.groq.com/keys) (used for LLM inference)

### Backend

```bash
git clone <this-repo-url>
cd ContextIQ/backend

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp ../.env.example .env
```

Edit `backend/.env` and fill in:

- `SECRET_KEY` — any random string (used to sign JWTs)
- `DB_ENCRYPTION_KEY` — generate with:
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
  Used to encrypt saved external-database connection strings at rest. Keep it stable — rotating it makes existing saved connections undecryptable.
- `GROQ_API_KEY` — from the Groq link above

`DATABASE_URL` defaults to a local SQLite file (`sqlite:///./contextiq.db`) and needs no setup. `FRONTEND_ORIGIN` defaults to `http://localhost:5173`, matching the frontend dev server below.

Run the API:

```bash
uvicorn main:app --reload
```

The backend serves at `http://localhost:8000` (interactive API docs at `/docs`).

### Frontend

```bash
cd ContextIQ/frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL defaults to http://localhost:8000
npm run dev
```

The frontend serves at `http://localhost:5173`.

### Running tests

```bash
cd ContextIQ
pytest backend/tests/ -v
```

## Known limitation: scanned PDFs

ContextIQ does not currently perform OCR. If you upload a scanned/image-based PDF (one with no extractable text layer), the upload is rejected with a clear `422` error explaining why, rather than silently indexing an empty document you'd only discover later when every question about it came back "I couldn't find anything relevant." Adding OCR support would require the system `tesseract` binary (not pip-installable) plus the `pytesseract` and `PyMuPDF` packages — none of which are part of this project yet. See `backend/loaders/document_loader.py` for the detection logic and exact error message.

## Evaluation

Retrieval quality is benchmarked in [`eval/`](eval/): Precision@K, Recall@K, MRR, and MAP, plus p50/p95 latency, computed for three retriever configurations — FAISS-only, BM25-only, and the hybrid Ensemble — against a labeled question set spanning all five supported file types, including questions specifically designed to need exact numbers or rare terms (the case hybrid retrieval exists for). BM25-only measurably underperforms on exact-value lookups that the hybrid retriever recovers; see [`eval/results_baseline_k4.md`](eval/results_baseline_k4.md) for the full breakdown and [`eval/weight_tuning_summary.md`](eval/weight_tuning_summary.md) for an ensemble-weight sensitivity sweep. The eval set and methodology (including its current caveats and known limitations) are documented in [`eval/eval_set.json`](eval/eval_set.json) and [`eval/README.md`](eval/README.md) — read those before citing any numbers, as they explain exactly what the benchmark does and doesn't demonstrate.

## Deployment

Planned (Render + Vercel), instructions coming soon.
