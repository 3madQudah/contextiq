# 16 — Style Guide

Conventions as **observed in the repo**, not aspirational. Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §9.5 and files read directly.

Related: [15 — Contributing](15-CONTRIBUTING.md) · [04 — Architecture](04-ARCHITECTURE.md)

---

## Part A — Code conventions

### A.1 Python (backend)

- **Module layout:** one responsibility per module; every module opens with a triple-quoted docstring explaining its role and cross-referencing related modules (e.g. `sql_chain.py`, `csv_compute.py`). Constants are UPPER_SNAKE at module top (`FETCH_K`, `TOP_K`, `MAX_DOCUMENT_CHARS`, `DEFAULT_ROW_LIMIT`).
- **Naming:** `snake_case` functions/variables; `PascalCase` classes and Pydantic/ORM models; leading underscore for module-private helpers (`_index_path`, `_classify_operational_error`, `_format_chunk_header`).
- **Docstrings & comments:** functions carry short docstrings stating intent and edge behavior. Non-obvious decisions are explained inline with the *why*, often at length (see the read-only-connection and error-classification comments in `sql_chain.py`). Match this density — comments explain rationale, not mechanics.
- **Typing:** type hints throughout (`Optional`, `List`, `Dict`, `Tuple`); dataclasses for internal plans (`ComputePlan`, `DocumentPlan`, `PDFExtract`).
- **Error handling:**
  - Domain errors are custom exceptions (`ScannedPDFError`, `SQLValidationError` with a `layer`, `SQLExecutionTimeout`, `SQLConnectionError`).
  - Routes translate them to `HTTPException(status_code=…, detail=…)` with an accurate code (see [06 — API Specification](06-API-SPECIFICATION.md)); all error bodies use `{"detail": …}`.
  - Compute paths return `None` to signal "fall back to RAG" rather than raising.
  - Failures are logged with `logger.exception` / `logger.warning` at the point of classification before re-raising; the LLM path never fabricates an answer on failure (raises `502`).
- **FastAPI:** dependencies for auth/ownership (`Depends(get_current_user)`, `Depends(get_owned_*)`); Pydantic request/response models defined near the route or in `auth/schemas.py`.
- **Config:** read via `os.getenv("NAME", default)` with `load_dotenv()` at module import; defaults chosen to work locally (see [03 §4](03-TECHNICAL-SPECIFICATION.md)).

### A.2 JavaScript / React (frontend)

- **Components:** function components, default-exported, one per file, `PascalCase` filenames (`MessageBubble.jsx`). Hooks and helpers are `camelCase`.
- **State:** React Context for cross-cutting state (`AuthContext`, `AppDataContext`, `ThemeContext`, `ToastContext`); each exposes a `useX()` hook that throws if used outside its provider. No Redux.
- **API access:** all backend calls go through the single axios client in `services/api.js`; components never call axios directly. Errors are normalized with `getErrorMessage(err, fallback)`.
- **Imports:** external packages first, then local modules; relative paths with explicit `.jsx`/`.js` extensions.
- **Comments:** like the backend, comments explain *why* (e.g. the `localStorage` rationale, the upload-serialization note, the `useMatch`-not-`useParams` note in `Sidebar.jsx`). Keep that intent-first style.
- **Routing:** `react-router-dom` v6; route gates are components (`ProtectedRoute`, `PublicOnlyRoute`) rendered as layout routes.

## Part B — Design system (as implemented)

From `frontend/src/index.css`, `tailwind.config.js` (audit §9.5).

### B.1 Color tokens (CSS variables, RGB triplets)

Consumed via Tailwind as `rgb(var(--x) / <alpha-value>)`, enabling opacity modifiers (e.g. `bg-accent/10`). Hex equivalents shown for reference.

| Token | Light (RGB → hex) | Dark (RGB → hex) |
|---|---|---|
| `bg` | `250 250 250` → `#FAFAFA` | `9 9 11` → `#09090B` |
| `surface` | `255 255 255` → `#FFFFFF` | `24 24 27` → `#18181B` |
| `surface-hover` | `244 244 245` → `#F4F4F5` | `39 39 42` → `#27272A` |
| `border` | `228 228 231` → `#E4E4E7` | `39 39 42` → `#27272A` |
| `foreground` | `24 24 27` → `#18181B` | `244 244 245` → `#F4F4F5` |
| `muted` | `113 113 122` → `#71717A` | `161 161 170` → `#A1A1AA` |
| `accent` | `79 70 229` → `#4F46E5` | `129 140 248` → `#818CF8` |
| `accent-foreground` | `255 255 255` → `#FFFFFF` | `9 9 11` → `#09090B` |
| `danger` | `220 38 38` → `#DC2626` | `248 113 113` → `#F87171` |
| `danger-foreground` | `255 255 255` → `#FFFFFF` | `9 9 11` → `#09090B` |
| `success` | `22 163 74` → `#16A34A` | `74 222 128` → `#4ADE80` |
| `aurora-violet` (decorative only) | `168 85 247` → `#A855F7` | `192 132 252` → `#C084FC` |
| `aurora-cyan` (decorative only) | `34 211 238` → `#22D3EE` | `103 232 249` → `#67E8F9` |
| `pipeline-surface` | `238 237 254` → `#EEEDFE` | `34 30 58` → `#221E3A` |
| `pipeline-border` | `127 119 221` → `#7F77DD` | `148 140 240` → `#948CF0` |
| `pipeline-label` | `60 52 137` → `#3C3489` | `199 195 255` → `#C7C3FF` |

- Palette: one accent (indigo), everything else neutral (zinc scale). Theme via `.dark` class on `<html>`.
- Aurora hues are **decorative only** (background glow/blobs), never used for text.

### B.2 Typography

Font stack: `-apple-system, BlinkMacSystemFont, Inter, Segoe UI, Helvetica Neue, Arial, sans-serif`.

Scales are **replaced** (not extended) in Tailwind to enforce "two weights, six sizes" for in-app UI:

- In-app sizes: `xs 12/16`, `sm 13/18`, `base 14/20`, `md 16/24`, `lg 20/28`, `xl 24/32` (px, size/line-height).
- Marketing-only sizes: `2xs 11.5`, `display-xs 30`, `display-sm 32`, `display-md 44`.
- Weights: `normal 400`, `medium 500` (in-app); `semibold 600`, `bold 700` (marketing only).
- Consequence: a stray `text-2xl`/`text-3xl` or `font-bold` in app UI resolves to nothing — the constraint is enforced by the config.

### B.3 Radius, shadow, blur

- Radius: `md 6px`, `lg 8px`, `xl 12px`, `2xl 18px`.
- Shadows: `glass`, `glass-lg`, `glow` (accent-tinted).
- Backdrop blur: `xs 2px`. `.glass-panel` = translucent surface + backdrop blur + gradient.

### B.4 Animation

- Keyframes/animations: `aurora-drift` (18s) / `-slow` (26s reverse), `shimmer` (2s), and pipeline set (`flow`, `hub`, `ripple`, `line-in`, `pill-in`, `card-in`).
- Motion tokens shared in `lib/motion.js` (`easeOut`, spring presets, page/stagger/message variants).
- Reduced motion respected globally via `<MotionConfig reducedMotion="user">` and `@media (prefers-reduced-motion: reduce)` in `index.css` (disables aurora/skeleton/pipeline animations).

### B.5 Component conventions

- Buttons (`Button.jsx`): variants `primary`, `secondary`, `ghost`, `danger`, `invert`; loading spinner; motion hover/tap.
- Inputs (`TextInput`, `PasswordInput`, `Select`): shared `{label, error, hint}` shape; visible focus ring (`:focus-visible` outline `2px accent`, offset 2px) — never suppress focus rings without a replacement.
- Feedback: inline errors/empty-states are the source of truth; toasts (`ToastContext`) are additive only.
- Markdown answers rendered via `react-markdown` + `remark-gfm` inside `.markdown-body`.

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
