# 04 — Architecture

Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §4, §6.4, §8, §14.3.

Related: [03 — Technical Specification](03-TECHNICAL-SPECIFICATION.md) · [05 — Data Model](05-DATA-MODEL.md) · [06 — API Specification](06-API-SPECIFICATION.md)

---

## 1. System overview

ContextIQ is a two-tier application: a React SPA (served statically) and a FastAPI backend. The backend owns an app database (SQLite/Postgres), per-user on-disk retrieval indexes (FAISS + BM25), and calls out to the Groq API for LLM inference and to user-provided external SQL databases for the text-to-SQL feature.

```mermaid
graph TD
  subgraph Client
    SPA["React SPA (Vite build)<br/>axios + JWT in localStorage"]
  end

  subgraph Backend["FastAPI backend"]
    MW["Middleware: SlowAPI + CORS"]
    R1["api/auth_routes"]
    R2["api/documents_routes"]
    R3["api/chat_routes"]
    R4["api/conversations_routes"]
    R5["api/databases_routes"]
    CHAIN["chain/* (RAG, compute, sql_chain)"]
    ING["ingestion/* + loaders/*"]
  end

  subgraph Storage
    DB[("App DB<br/>SQLite/Postgres")]
    IDX["Per-user FAISS + BM25<br/>data/vector_index/{user_id}/"]
    RAW["Raw uploads<br/>data/raw/{user_id}/"]
  end

  subgraph External
    GROQ["Groq API (LLM)"]
    USERDB[("User external SQL DB<br/>Postgres/MySQL/SQLite (read-only)")]
  end

  SPA --> MW --> R1 & R2 & R3 & R4 & R5
  R1 --> DB
  R2 --> ING --> IDX & RAW
  R3 --> CHAIN
  R4 --> DB
  R5 --> CHAIN
  CHAIN --> IDX
  CHAIN --> GROQ
  CHAIN --> USERDB
  R3 --> DB
  R5 --> DB
```

## 2. Application assembly & middleware order

On import, `main.py` (audit §4.1):

1. `load_dotenv()`.
2. Imports all ORM model modules (registers tables on the shared `Base.metadata`).
3. `Base.metadata.create_all(bind=engine)` — creates tables if missing (no migration tool; see [05 — Data Model](05-DATA-MODEL.md)).
4. Builds `FastAPI(title="ContextIQ")`, registers the slowapi limiter + `RateLimitExceeded` handler, adds `SlowAPIMiddleware`, then `CORSMiddleware` (`allow_origins=[FRONTEND_ORIGIN]`, credentials on, methods/headers `*`).
5. Mounts routers under `/api/auth`, `/api/documents`, `/api/chat`, `/api/conversations`, `/api/databases`; adds `GET /health`.

**Middleware** (audit §4.2): `SlowAPIMiddleware` (added first), then `CORSMiddleware`. There is **no custom auth middleware** — authentication is per-route via the `get_current_user` dependency. Auth rate limits are additionally applied per-route via `@limiter.limit(...)`.

There are **no** startup/shutdown event handlers beyond `create_all` at import time, and **no** background tasks, schedulers, or async jobs (audit §4.5).

## 3. Request lifecycle — `POST /api/chat/ask`

```mermaid
sequenceDiagram
  actor U as Browser (SPA)
  participant MW as SlowAPI + CORS
  participant H as chat_routes.ask
  participant Dep as get_current_user / get_db
  participant DB as App DB
  participant P as Routing (compute / full-doc / RAG)
  participant G as Groq API

  U->>MW: POST /api/chat/ask (Bearer JWT)
  MW->>Dep: resolve dependencies
  Dep->>DB: decode JWT, load User; open session
  Dep-->>H: current_user, db
  alt conversation_id is null
    H->>DB: create + commit Conversation
  else
    H->>DB: get_owned_conversation_by_id (404 if not owned)
  end
  H->>DB: persist user Message (committed before LLM call)
  H->>P: route question
  Note over P: 1) CSV compute if csv+computational<br/>2) full-doc if docx/pdf/md classifier fires<br/>3) else RAG
  P->>G: LLM call(s) (temperature=0)
  alt any exception
    H-->>U: 502 (user message kept, no fake assistant message)
  else success
    H->>DB: persist assistant Message + sources; bump updated_at; commit
    H-->>U: 200 ChatResponse (answer, sources, conversation_id, rewritten_query)
  end
```

## 4. Ingestion pipeline

```mermaid
flowchart TD
  A["POST /api/documents/upload"] --> B{is_supported_file?}
  B -- no --> B1["400 Unsupported file type"]
  B -- yes --> C["Save to data/raw/{user_id}/{filename}"]
  C --> D["load_document (dispatch by extension)"]
  D --> D1{".pdf scanned?<br/>≥80% pages <20 chars"}
  D1 -- yes --> D2["422 ScannedPDFError (file kept, not indexed)"]
  D1 -- no --> E["chunk_documents<br/>size=1000, overlap=150<br/>tag user_id/file_name/file_type/section_heading"]
  E --> F["get_embeddings()<br/>all-MiniLM-L6-v2 (cached)"]
  F --> G["build_faiss_index<br/>load+add or from_documents; save_local"]
  G --> H["save_chunks → chunks.pkl (append)"]
  H --> I["201 {filename, chunks_indexed}"]
```

Loaders (`loaders/document_loader.py`): PDF via `PyPDFLoader` + scan detection; DOCX/MD section-aware (`section_heading` metadata); TXT/CSV via LangChain community loaders. Delete path drops the file's chunks from `chunks.pkl` then **rebuilds** the FAISS index from the remaining chunks — O(remaining chunks) per delete (documented caveat, §7).

## 5. Retrieval / answering pipeline (RAG path)

```mermaid
flowchart TD
  A["run_rag_chain(user_id, question, history, file_type, file_name)"] --> B{"history present?"}
  B -- yes --> C["rewrite_query → standalone query (Groq)"]
  B -- no --> D["use question as-is"]
  C --> E["get_hybrid_retriever(user_id)"]
  D --> E
  E --> E0{"index exists?"}
  E0 -- no --> E1["'You haven't uploaded any documents yet…'"]
  E0 -- yes --> F["EnsembleRetriever [FAISS 0.5, BM25 0.5], k=8 each<br/>invoke → FETCH_K=8 candidates"]
  F --> G["filter_documents by file_type/file_name"]
  G --> H["keep TOP_K=4"]
  H --> H0{"any left?"}
  H0 -- no --> H1["'I couldn't find anything relevant…'"]
  H0 -- yes --> I["assemble context with [Source: … | Section: …]"]
  I --> J["select prompt: single file_type → tailored, else default"]
  J --> K["ChatGroq(temperature=0) → answer"]
  K --> L["sources = sorted unique file_name; return {answer, sources, rewritten_query}"]
```

Routing to CSV-compute or full-document paths happens **before** the RAG path in `chat_routes.ask` — see [02 — Product Specification §6](02-PRODUCT-SPECIFICATION.md).

## 6. Text-to-SQL pipeline

```mermaid
flowchart TD
  A["POST /api/databases/{id}/ask (ownership-verified)"] --> B["decrypt_connection_string (Fernet)"]
  B --> C["get_schema_snapshot (inspect; cached 60s)"]
  C --> D["format_schema_for_prompt"]
  D --> E["generate_sql (Groq) → strip fences"]
  E --> F["validate_sql: SELECT-only, no stacked query, no forbidden keywords"]
  F -- reject --> F1["400 (layer named)"]
  F -- ok --> G["execute_query over read-only connection + statement timeout"]
  G -- timeout --> G1["504 SQLExecutionTimeout"]
  G -- connection lost --> G2["503 SQLConnectionError"]
  G -- other --> G3["502 unclassified"]
  G -- ok --> H["fetch row_limit+1 → truncate to 200; serialize values"]
  H --> I["summarize_answer (Groq, ≤50 rows)"]
  I --> J["200 DBQueryResponse {answer, sql_query, columns, rows, row_count, truncated}"]
```

Read-only enforcement per DB type and error classification: [02 — Product Specification §8](02-PRODUCT-SPECIFICATION.md) and [13 — Security](13-SECURITY.md).

## 7. On-disk layout (non-relational state)

From audit §6.4:

```
backend/data/
├── raw/
│   └── {user_id}/
│       └── {original_filename}         # raw uploaded files, one dir per user
└── vector_index/
    └── {user_id}/
        ├── index.faiss                 # FAISS index (FAISS.save_local)
        ├── index.pkl                   # FAISS docstore/id map
        └── chunks.pkl                  # pickled LangChain Documents (backs BM25 + rebuild)
```

- `.gitkeep` files preserve the two directories; contents are gitignored.
- The only cache is in-process: the `sql_chain._schema_cache` (60s TTL, keyed by `connection_id`) and the embeddings singleton.
- FAISS `index.pkl` and `chunks.pkl` are loaded with `pickle` / `allow_dangerous_deserialization=True` — trusted as app-generated data (see [13 — Security](13-SECURITY.md)).
- Observed locally: an orphaned `vector_index/3/` exists with no matching `raw/3/` (audit §1.5).

## 8. Documented scaling caveats (audit §14.3)

| Caveat | Detail |
|---|---|
| No FAISS write locking | Per-user index is rebuilt on each write with no server-side lock; the frontend serializes uploads to avoid corruption. |
| O(N) document delete | Deleting one document re-embeds all remaining chunks for that user. |
| cwd-relative default DB path | `sqlite:///./contextiq.db` resolves relative to process cwd; docker-compose overrides it to a volume path to avoid data loss on rebuild. |
| Build-time API base URL | `VITE_API_BASE_URL` is compiled into the JS bundle; changing it requires a rebuild. |
| Single CORS origin | `FRONTEND_ORIGIN` allows exactly one origin. |

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
