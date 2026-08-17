# 13 — Security

Source of truth: [PROJECT-AUDIT.md](PROJECT-AUDIT.md) §7. This document states current mitigations honestly, including implemented gaps.

Related: [02 — Product Specification](02-PRODUCT-SPECIFICATION.md) · [09 — Decisions](09-DECISIONS.md) · [08 — Roadmap](08-ROADMAP.md)

---

## 1. Threat model (scope)

| Asset | Threat | Primary control |
|---|---|---|
| User accounts | Credential brute force | Password policy + IP rate limiting on register/login |
| Passwords at rest | DB compromise | bcrypt hashing (no plaintext) |
| Session tokens | Theft / replay | Short-lived signed JWT (default 60 min) |
| One user's documents/data | Cross-user access | Per-user indexes + ownership checks (404 on foreign id) |
| External DB credentials | Leak from app DB or API | Fernet encryption at rest; never returned by API |
| User's external database | LLM-generated writes / injection | Regex validation + read-only connection + timeout + row cap |

Out of scope for this version: server-side token revocation, WAF/DDoS protection, secret-manager integration, audit logging.

## 2. Authentication flow

- **Register** (`POST /api/auth/register`): validates email + password strength → hashes password (bcrypt) → inserts `User`. No token issued, no email verification; the frontend logs in immediately afterward (audit §7.1).
- **Login** (`POST /api/auth/login`): verifies email + password → issues JWT. Wrong credentials → generic `401` (no field disclosure) (audit §7.2).

## 3. Token handling

- Creation (`auth/jwt_handler.py`): `jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)`; claims `sub` (user id) + `exp` (`now(utc) + ACCESS_TOKEN_EXPIRE_MINUTES`, default 60). Algorithm `HS256`. No refresh tokens.
- Verification (`api/dependencies.get_current_user`): extracts Bearer via `HTTPBearer`, decodes, loads `User` by `sub`; any failure → `401` "Could not validate credentials" with `WWW-Authenticate: Bearer`.
- Client storage: token + minimal user object in `localStorage`; attached as a Bearer header by an axios interceptor. A `401` from any non-auth endpoint clears the token and redirects to `/login` (audit §9.3, §9.4).

## 4. Password hashing & policy

- Hashing: passlib `CryptContext(schemes=["bcrypt"], deprecated="auto")`; bcrypt default cost (factor 12). `bcrypt` pinned `<4.1` for passlib compatibility (audit §7.4).
- Policy (server-enforced, `auth/schemas.py`): ≥ 12 chars, ≥ 1 uppercase, ≥ 1 lowercase, ≥ 1 digit, ≥ 1 of `!@#$%^&*()_+-=` (audit §7.5). Mirrored client-side for UX only.

## 5. Per-user isolation

From audit §7.6:

- **Retrieval:** separate FAISS + BM25 indexes keyed by `user_id`; a different index is loaded per user. The metadata filter only narrows within a user's own docs — it is not the isolation boundary.
- **Conversations / connections:** `get_owned_conversation_by_id` / `get_owned_connection_by_id` filter on `id AND user_id`; missing OR foreign → `404` (indistinguishable, no existence leak).
- **Documents:** keyed by `data/raw/{current_user.id}/`.

## 6. Rate limiting

`slowapi`, keyed by client IP: `5/15minutes` on `POST /api/auth/register` and `POST /api/auth/login`. `429` response uses the app-wide `{"detail": …}` shape. No other route is limited (audit §7.7).

## 7. Encryption at rest

- Fernet (AES-128-CBC + HMAC, `cryptography`) encrypts `DatabaseConnection.encrypted_connection_string` (audit §7.8).
- Key from `DB_ENCRYPTION_KEY`; unset → `RuntimeError` at use. Rotating the key makes existing ciphertexts undecryptable (`ValueError` on `InvalidToken`).
- Decrypted strings are never logged or returned; `ConnectionSummary` excludes them.

## 8. SQL injection / write defenses (text-to-SQL)

Defense-in-depth (`chain/sql_chain.py`, audit §7.9):

1. **Text validation** (`validate_sql`): strip `/* */` and `--` comments; must start with `SELECT`; reject stacked queries; reject forbidden keywords (`INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, REVOKE, EXEC, EXECUTE, ATTACH, DETACH, PRAGMA, CREATE, REPLACE, MERGE, CALL, VACUUM, REINDEX, COPY, OUTFILE, DUMPFILE, LOAD_FILE`); errors tagged with the failing `layer`.
2. **Read-only connection:** sqlite `file:…?mode=ro`; Postgres `postgresql_readonly=True`; MySQL `SET SESSION TRANSACTION READ ONLY`.
3. **Statement timeout** (10s) and **row cap** (200).
4. **Prompt guard:** on modification requests, the model is told to emit `SELECT 1 WHERE 1=0`.

The CSV computational path is also injection-safe by construction: no user text reaches `eval`/`exec`/`DataFrame.query`; only a closed operation set and real column names are used (audit §8.3).

## 9. Known limitations (unflinching)

Reproduces audit §7.10 / §14.3. Each with current mitigation and planned fix.

| # | Limitation | Current mitigation | Planned fix |
|---|---|---|---|
| S1 | **`.env.example` contains real-looking committed secrets** (`SECRET_KEY`, `DB_ENCRYPTION_KEY`, `GROQ_API_KEY`) | None — values are in the committed file | **Rotate all three immediately; replace with placeholders** ([08 §N1](08-ROADMAP.md)) |
| S2 | Insecure `SECRET_KEY` fallback (`"insecure-dev-secret-change-me"`) if env unset | Documented; overridden in real `.env` | Remove the default; fail fast if unset ([08 §N2](08-ROADMAP.md)) |
| S3 | No server-side token revocation / refresh | Short 60-min expiry | Add refresh + revocation ([08 §L3](08-ROADMAP.md)) |
| S4 | JWT in `localStorage` (XSS-readable) | No known XSS; SPA is self-authored | Consider httpOnly cookie ([08 §L4](08-ROADMAP.md), [ADR-005](09-DECISIONS.md)) |
| S5 | FAISS `index.pkl` + `chunks.pkl` loaded via pickle / `allow_dangerous_deserialization=True` | Data is app-generated and local (trusted disk) | Restrict/validate index provenance if ever shared |
| S6 | SQL validation is regex-level, not a real parser | Read-only connection is the real write guard (defense-in-depth) | Optionally add a SQL parser layer ([ADR-004](09-DECISIONS.md)) |
| S7 | No upload size cap on `/api/documents/upload` | None | Enforce a size limit ([08 §N6](08-ROADMAP.md)) |
| S8 | `file.filename` used directly in the raw path join (no explicit traversal sanitization) | Ext allow-list; per-user directory | Sanitize/normalize the filename ([08 §N7](08-ROADMAP.md)) |
| S9 | Single-origin CORS (`FRONTEND_ORIGIN`) | Intentional for a single frontend | Multi-origin support if needed ([08 §L5](08-ROADMAP.md)) |
| S10 | MariaDB statement timeout not enforced | Postgres/MySQL/SQLite are enforced; app-level validation still applies | Detect MariaDB, use `max_statement_time` ([08 §M7](08-ROADMAP.md)) |

> S1 is the highest priority and blocks any public deployment ([11 — Checkpoint](11-CHECKPOINT.md), [14 — Deployment](14-DEPLOYMENT.md)).

---

Author: Emad Al-Qadah · qudahemad@yahoo.com · [github.com/3madQudah](https://github.com/3madQudah) · [linkedin.com/in/emadalqudah](https://www.linkedin.com/in/emadalqudah)
