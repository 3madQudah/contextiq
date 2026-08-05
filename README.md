# ContextIQ

A Retrieval-Augmented Generation (RAG) system with user authentication.

## Phase 1 scope
- JWT-based authentication (register/login)
- Document ingestion (loading, chunking, embedding)
- FAISS-backed vector store
- Basic RAG chat pipeline over uploaded documents

## Tech stack
**Backend:** Python, FastAPI, SQLAlchemy, SQLite, JWT auth (python-jose, passlib, bcrypt), LangChain, FAISS (faiss-cpu), sentence-transformers

**Frontend:** React (Vite), Tailwind CSS, axios, react-router-dom

## Project structure
```
backend/    FastAPI app: auth, API routes, ingestion pipeline, RAG chain
frontend/   React SPA: auth pages, dashboard, chat UI
```

## Getting started
This is a structural scaffold (Phase 1) — no business logic implemented yet.

1. Copy `.env.example` to `.env` and fill in values.
2. Backend: `cd backend && pip install -r requirements.txt`
3. Frontend: `cd frontend && npm install`
# contextiq
