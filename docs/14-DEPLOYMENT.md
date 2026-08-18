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

## 6. Render (backend) + Vercel (frontend) — procedure

Target: **Render free web service + Render free Postgres** for the backend, **Vercel** for the frontend. Backend hosting config lives in [`render.yaml`](../render.yaml) (repo root); frontend config in [`frontend/vercel.json`](../frontend/vercel.json). No persistent disk is used — this is an accepted trade-off (see §6.5).

### 6.1 Backend on Render

The [`render.yaml`](../render.yaml) blueprint declares one `docker` web service (`plan: free`, `dockerfilePath: ./backend/Dockerfile`, `dockerContext: ./backend`, `healthCheckPath: /health`) and one free Postgres database (`contextiq-db`).

1. Create a Render Blueprint from the repo (or a Docker web service pointing at `backend/Dockerfile`). The blueprint provisions the free Postgres and wires `DATABASE_URL` to it automatically.
2. The container start command honours Render's dynamic `$PORT` (`backend/Dockerfile` uses a shell-form `CMD` with `--port ${PORT:-8000}` and `--host 0.0.0.0`). Single worker — do **not** add `--workers`; the per-user FAISS index has no concurrency locking (audit §14.3).
3. Render uses the service's Health Check Path `/health` (`main.py:52`).

**Env vars to set in the Render dashboard** (all `sync: false` in `render.yaml` — enter values by hand, never commit them):

| Variable | Required | Value |
|---|---|---|
| `SECRET_KEY` | Yes | A fresh random secret (rotated — see §7) |
| `DB_ENCRYPTION_KEY` | Yes | A fresh Fernet key (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) |
| `GROQ_API_KEY` | Yes | Your Groq API key |
| `FRONTEND_ORIGIN` | Yes | The Vercel origin (set in pass 2 — see §6.4) |
| `ALGORITHM` | No | Defaults to `HS256` in code if unset |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Defaults to `60` |
| `GROQ_MODEL_NAME` | No | Defaults to `llama-3.1-8b-instant` |
| `GROQ_REWRITE_MODEL_NAME` | No | Defaults to `llama-3.1-8b-instant` |

`DATABASE_URL` is **not** entered by hand: it is wired from the Render Postgres via `fromDatabase` in the blueprint, so it can never fall back to the ephemeral SQLite default (`database.py:18`; `postgres://` is normalized to `postgresql://` automatically). Schema is created at startup via `create_all` — there are no Alembic migrations yet (see [ADR-006](09-DECISIONS.md)), which is acceptable for a single-schema demo but must be addressed before evolving a populated DB.

### 6.2 Frontend on Vercel

[`frontend/vercel.json`](../frontend/vercel.json) sets `buildCommand: npm run build`, `outputDirectory: dist`, and an SPA rewrite (`/(.*)` → `/index.html`) so client-side routes don't 404 on refresh. Vercel serves the static build directly — the `frontend/Dockerfile` and `frontend/nginx.conf` are for the Docker Compose path and are **not** used on Vercel.

**Env var to set in the Vercel project** (Settings → Environment Variables):

| Variable | When | Value |
|---|---|---|
| `VITE_API_BASE_URL` | **Build time** | The Render backend URL, e.g. `https://contextiq-backend.onrender.com` |

`VITE_API_BASE_URL` is compiled into the JS bundle at build time (`services/api.js:3`). Changing it requires a **rebuild/redeploy on Vercel**, not just a restart — a redeploy that reuses the existing build output will not pick up a new value.

### 6.3 Cross-cutting (still open)

- [ ] CI (lint + `pytest backend/tests/`) — none exists ([08 — Roadmap](08-ROADMAP.md) N5).
- [ ] Upload size cap + `file.filename` sanitization before public exposure ([13 — Security](13-SECURITY.md) S7/S8).
- TLS is terminated by Render and Vercel at their edges (both serve HTTPS by default).

### 6.4 The `FRONTEND_ORIGIN` ↔ Vercel-origin ↔ CORS ordering problem

CORS on the backend allows exactly one origin, `FRONTEND_ORIGIN` (`main.py:29,37-43`), and the frontend needs the backend URL baked in at build time (`VITE_API_BASE_URL`). The Vercel production URL is **not known until the frontend's first deploy**, which creates a chicken-and-egg. Resolve it in two passes:

**Pass 1 — backend first**
1. Deploy the backend on Render. Note its URL, e.g. `https://contextiq-backend.onrender.com`.
2. Leave `FRONTEND_ORIGIN` at a placeholder for now (the frontend won't pass CORS yet — expected).

**Pass 2 — frontend, then close the loop**
3. Deploy the frontend on Vercel with `VITE_API_BASE_URL` set to the backend URL from step 1. Note the resulting Vercel origin, e.g. `https://contextiq.vercel.app`.
4. Set `FRONTEND_ORIGIN` on Render to that Vercel origin and let the backend restart (an env change triggers a restart). CORS now admits the frontend.

**On later changes:** if the backend URL changes, you must **rebuild the frontend** (build-time `VITE_API_BASE_URL`), not just redeploy. If the frontend origin changes (e.g. a custom domain), update `FRONTEND_ORIGIN` on Render.

### 6.5 Data persistence — known limitation

Render free web services **cannot attach a persistent disk**, so this deployment runs without one (accepted trade-off):

- **Ephemeral filesystem.** Everything under `/app/data` — per-user FAISS indexes (`index.faiss`/`index.pkl`), BM25 `chunks.pkl`, and raw uploaded files — lives on the container's writable layer.
- **Redeploy/restart wipe.** That layer is reset on every deploy and on every restart or instance replacement. Uploaded documents and their indexes do not survive; users must re-upload.
- **Free Postgres expiry.** Accounts, conversations, messages, and saved DB connections persist in the free Render Postgres, but free Postgres instances are time-limited and are removed by Render after their expiry window — treat that data as disposable too.
- **The fix** is object storage (S3 or equivalent) for uploads and indexes, tracked as the top near-term item ([08 — Roadmap](08-ROADMAP.md) N0). The in-app [`DemoBanner`](../frontend/src/components/DemoBanner.jsx) states this limitation to users.

## 7. Pre-deployment checklist

1. [ ] **Rotate the leaked secrets** (`SECRET_KEY`, `DB_ENCRYPTION_KEY`, `GROQ_API_KEY`) committed in `.env.example`, and replace them with placeholders. **Blocking — do this first** ([13 — Security](13-SECURITY.md) S1).
2. [ ] Remove the insecure `SECRET_KEY` fallback default.
3. [ ] Render Blueprint applied; free Postgres provisioned; `DATABASE_URL` wired from it (not SQLite).
4. [ ] Backend env vars set in the Render dashboard (§6.1 table).
5. [ ] Frontend deployed on Vercel with build-time `VITE_API_BASE_URL` (§6.2).
6. [ ] Two-pass origin wiring done: `FRONTEND_ORIGIN` set to the Vercel origin and backend restarted (§6.4).
7. [ ] `/health` (backend) returns OK; the SPA loads and can call the API without CORS errors.
8. [ ] Users informed of the ephemeral-data limitation (the in-app `DemoBanner` covers this) (§6.5).
9. [ ] (Follow-up) CI green on `pytest backend/tests/`; upload size cap + filename sanitization added.

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
