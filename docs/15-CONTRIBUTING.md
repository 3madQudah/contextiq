# 15 — Contributing

Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md). Conventions below reflect what the repo actually does.

Related: [12 — Testing](12-TESTING.md) · [16 — Style Guide](16-STYLEGUIDE.md) · [04 — Architecture](04-ARCHITECTURE.md)

---

## 1. Repository layout

```
ContextIQ/
├── backend/      FastAPI app (api, auth, chain, ingestion, loaders, prompt_eng, utils, tests, data)
├── frontend/     React + Vite SPA (src/{pages,components,context,lib,services})
├── eval/         Retrieval evaluation harness + fixtures + results
└── docs/         Documentation set (this directory)
```

Module responsibilities: [03 §5](03-TECHNICAL-SPECIFICATION.md). On-disk data layout: [04 §7](04-ARCHITECTURE.md).

## 2. Dev setup

Backend and frontend setup: [14 — Deployment §1](14-DEPLOYMENT.md). In short: Python venv + `pip install -r backend/requirements.txt` + `.env`; `npm install` in `frontend/`. Run `uvicorn main:app --reload` and `npm run dev`.

## 3. Branch & commit conventions

- Default branch: `main`. Do not commit directly to `main` for non-trivial work — branch first.
- Commit messages: short imperative subject describing the change set (the existing history uses descriptive subjects, e.g. "Add hybrid retrieval evaluation, per-file-type prompts, computational query paths, and project documentation").
- Keep secrets out of commits. `.env`, `*.db`, and `backend/data/*` are gitignored — **never** commit real credentials (note the outstanding `.env.example` secret-rotation item in [13 — Security](13-SECURITY.md)).

## 4. How to add a new supported file type

A file type is wired through several layers. To add one (call it `xyz`), change **all** of:

1. **`backend/utils/helpers.py`** — add the extension to `SUPPORTED_EXTENSIONS`.
2. **`backend/loaders/document_loader.py`** — add loading logic: either register a loader in `LOADER_MAP` or add a dedicated `load_xyz_*` function and dispatch it in `load_document`.
3. **`backend/ingestion/chunking.py`** — no change needed for basic types (metadata `file_type` is derived from the extension), but confirm any custom metadata survives the split.
4. **`backend/prompt_eng/xyz_prompt.py`** — add a per-type prompt template, and register it in `prompt_eng/__init__.py`'s `PROMPT_REGISTRY` under key `"xyz"`.
5. **(Optional) compute path** — if the type needs exact/structural answers: add `backend/chain/xyz_query_classifier.py` (regex gate) and `backend/chain/xyz_compute.py` (compute-first, LLM-phrases-only, fall back with `None`), then wire it into `backend/api/chat_routes.py` (`FULL_DOCUMENT_HANDLERS` or a dedicated branch like CSV).
6. **`frontend/src/lib/fileTypes.js`** — add the extension to `ACCEPTED_EXTENSIONS` and an icon in `ICON_BY_EXTENSION`.
7. **`backend/tests/`** — add tests mirroring the existing `test_{csv,docx,pdf,md}_compute.py` / loader tests.

## 5. How to add an endpoint

1. Add the handler to the appropriate `backend/api/*_routes.py` (or create a new router module and `include_router` it in `backend/main.py` with a prefix).
2. Define request/response Pydantic schemas inline (as existing routes do) or in `auth/schemas.py` for auth.
3. Enforce auth with `current_user: User = Depends(get_current_user)`; for resource-scoped routes use the ownership dependencies (`get_owned_conversation`, `get_owned_connection`) so foreign ids `404`.
4. Raise `HTTPException` with an accurate status code and a `{"detail": …}`-shaped message (see [06 — API Specification](06-API-SPECIFICATION.md) for the codes in use).
5. Add a wrapper in `frontend/src/services/api.js` and wire the UI.
6. Add tests.

## 6. Test requirements before a PR

- `pytest backend/tests/` must pass (currently **58 passing** — [12 — Testing](12-TESTING.md)).
- New behavior needs tests: compute paths → correctness + fallback; routes → auth + ownership + error codes; validators → accept/reject cases.
- There is no CI yet (audit §14.4), so run the suite locally before opening a PR.
- There is no configured frontend test runner today; frontend changes are verified manually.

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
