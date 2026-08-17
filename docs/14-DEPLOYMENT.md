# 14 — Deployment

Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §13, §14.4.

Related: [03 — Technical Specification](03-TECHNICAL-SPECIFICATION.md) · [07 — Implementation Plan](07-IMPLEMENTATION-PLAN.md) · [13 — Security](13-SECURITY.md)

---

## 1. Local run (non-Docker)

### Backend

```bash
cd ContextIQ/backend
python3 -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env        # then set SECRET_KEY, DB_ENCRYPTION_KEY, GROQ_API_KEY
uvicorn main:app --reload      # http://localhost:8000 (docs at /docs)
```

Generate a Fernet key for `DB_ENCRYPTION_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Frontend

```bash
cd ContextIQ/frontend
npm install
cp .env.example .env            # VITE_API_BASE_URL defaults to http://localhost:8000
npm run dev                      # http://localhost:5173
```

### Tests

```bash
cd ContextIQ && pytest backend/tests/ -v
```

## 2. Docker Compose

```bash
cp .env.example .env             # fill SECRET_KEY, DB_ENCRYPTION_KEY, GROQ_API_KEY
docker-compose up --build
```

- Backend: 2-stage image (`python:3.11-slim`), pre-downloads the embedding model, runs as non-root `appuser`, healthcheck on `/health`.
- Frontend: 2-stage build (`node:20-slim` → `nginx:1.27-alpine`), serves `dist/`, healthcheck on `/healthz`, `depends_on` backend healthy.
- The backend container's `DATABASE_URL` is overridden to `sqlite:////app/data/contextiq.db` (inside the `backend_data` named volume) unless `DOCKER_DATABASE_URL` is set — this avoids the cwd-relative default writing outside the volume and being lost on rebuild (audit §14.3).
- `VITE_API_BASE_URL` is a build ARG, baked into the JS bundle; it must be **browser-reachable** (e.g. `http://localhost:8000`), never the internal Docker service name. Changing it requires a rebuild.

## 3. Ports

| Service | Port |
|---|---|
| Backend API | 8000 |
| Frontend dev server | 5173 |
| Frontend (Docker) | host 5173 → nginx 80 |
| External user DBs | per user-supplied connection string |

## 4. Required services & versions

- **Groq API** — required for any LLM answer (free key).
- **Embedding model** `sentence-transformers/all-MiniLM-L6-v2` — downloaded on first local use; pre-baked into the backend image.
- **App DB** — SQLite by default (no external service); optionally Postgres (`psycopg2-binary`) / MySQL (`PyMySQL`) via `DATABASE_URL`.
- Python 3.11+ (image 3.11); Node 18+ (build image 20).

## 5. Seed / setup

No DB seeding — tables are auto-created at startup via `create_all`. Only env config is required. First upload/question triggers a one-time embedding-model download (local runs).

---

## 6. Planned — not yet implemented (Render + Vercel)

README states deployment is "Planned (Render + Vercel), instructions coming soon" (audit §14.4). The following is a **target plan, not implemented**. No hosting config, migrations, CI, or secret-manager integration exists in the repo.

### 6.1 Backend (e.g. Render container)

- [ ] Provision managed **Postgres**; set `DATABASE_URL`. The code normalizes `postgres://` → `postgresql://`, so a Heroku-style URL works.
- [ ] **Introduce Alembic** and run migrations. Current startup uses `create_all`, which does not alter existing tables (see [ADR-006](09-DECISIONS.md)).
- [ ] Attach a **persistent volume** for `backend/data/` (per-user FAISS indexes, `chunks.pkl`, raw uploads). Without it, indexes and uploads are lost on redeploy. Ensure the container `DATABASE_URL` points inside the persistent path if staying on SQLite.
- [ ] Set the **env-var checklist**: `SECRET_KEY`, `DB_ENCRYPTION_KEY`, `GROQ_API_KEY`, `DATABASE_URL`, `FRONTEND_ORIGIN` (see [03 §4](03-TECHNICAL-SPECIFICATION.md)).
- [ ] Set **`FRONTEND_ORIGIN`** to the deployed frontend origin — CORS allows a single origin only (audit §14.3).

### 6.2 Frontend (e.g. Vercel / static host)

- [ ] Build with the correct **`VITE_API_BASE_URL`** pointing at the deployed backend. It is compiled into the bundle at build time — a runtime change requires a rebuild (audit §14.3).
- [ ] Serve `dist/` with SPA fallback (the provided `nginx.conf` already does `try_files … /index.html`).

### 6.3 Cross-cutting

- [ ] Add **CI** (lint + `pytest backend/tests/`) — none exists.
- [ ] Add an **upload size cap** and **filename sanitization** before public exposure ([13 — Security](13-SECURITY.md) S7/S8).
- [ ] Terminate **TLS** at the edge; no HTTPS config exists beyond nginx serving static assets.

## 7. Pre-deployment checklist

1. [ ] **Rotate the leaked secrets** (`SECRET_KEY`, `DB_ENCRYPTION_KEY`, `GROQ_API_KEY`) committed in `.env.example`, and replace them with placeholders. **Blocking — do this first** ([13 — Security](13-SECURITY.md) S1).
2. [ ] Remove the insecure `SECRET_KEY` fallback default.
3. [ ] Alembic migrations in place; schema matches.
4. [ ] Managed Postgres provisioned; `DATABASE_URL` set.
5. [ ] Persistent volume for `backend/data/` attached.
6. [ ] All env vars set (§6.1 checklist).
7. [ ] `FRONTEND_ORIGIN` and `VITE_API_BASE_URL` set to deployed origins.
8. [ ] `/health` and `/healthz` return OK.
9. [ ] Upload size cap + filename sanitization added.
10. [ ] CI green on `pytest backend/tests/`.

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
