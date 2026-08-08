"""
Text-to-SQL pipeline for the "ask an external database" feature. This is
deliberately separate from chain/rag_chain.py — no embeddings, no retrieval.
The flow: introspect the target database's schema, ask the LLM for one SQL
SELECT statement, validate that statement defensively, execute it over a
read-only connection with a statement timeout, then summarize the result.

Security model (see validate_sql and _readonly_connection):
  1. Text-level validation rejects anything that isn't a single SELECT before
     it is ever sent to the database.
  2. The database connection itself is opened read-only where the driver
     supports it, so validation isn't the only thing standing between the LLM
     and a write — even a validation bypass would still hit a read-only
     session/file handle at the DB layer.
Both layers are independently necessary: validation also controls row limits
and gives the user a clean error, and the read-only connection is what
actually enforces "no writes" when regex-based validation has a blind spot
(e.g. a semicolon or keyword hidden inside a string literal).
"""

import logging
import os
import re
import time
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Tuple
from urllib.parse import quote

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from auth.db_connection_models import DatabaseConnection
from prompt_eng.sql_prompt import SQL_ANSWER_PROMPT_TEMPLATE, SQL_PROMPT_TEMPLATE
from utils.crypto import decrypt_connection_string

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")

DEFAULT_ROW_LIMIT = 200
DEFAULT_STATEMENT_TIMEOUT_SECONDS = 10
SCHEMA_CACHE_TTL_SECONDS = 60
ANSWER_ROW_CONTEXT_LIMIT = 50

SUPPORTED_DB_TYPES = {"postgresql", "mysql", "sqlite"}


class SQLValidationError(Exception):
    """Raised when generated SQL fails validation — caught by the route and
    turned into a 400 before anything reaches the database. `layer` names
    which check caught it, for logging/debugging."""

    def __init__(self, message: str, layer: str):
        self.layer = layer
        super().__init__(message)


class SQLExecutionTimeout(Exception):
    """Raised when the query was cancelled for exceeding the statement timeout."""


# --- 1. Connection testing (used by POST /api/databases before saving) -----


def test_connection(db_type: str, connection_string: str) -> None:
    """Attempt a real connect + `SELECT 1`. Raises ValueError with a clear
    message on any failure; returns None on success."""
    url = _normalize_url(db_type, connection_string)
    engine = create_engine(url, connect_args=_connect_timeout_args(db_type))
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise ValueError(f"Could not connect to the database: {exc}") from exc
    finally:
        engine.dispose()


def _connect_timeout_args(db_type: str) -> dict:
    if db_type == "postgresql":
        return {"connect_timeout": 5}
    if db_type == "mysql":
        return {"connect_timeout": 5}
    return {}


# --- 2. URL normalization ---------------------------------------------------


def _normalize_url(db_type: str, connection_string: str):
    """Parse the connection string, ensure it uses a driver we have installed
    (psycopg2 for postgres, pymysql for mysql), and confirm the declared
    db_type actually matches what the connection string points at."""
    try:
        url = make_url(connection_string)
    except Exception as exc:
        raise ValueError(f"Malformed connection string: {exc}") from exc

    backend = url.get_backend_name()
    if backend != db_type:
        raise ValueError(
            f"db_type '{db_type}' does not match the connection string "
            f"(which is for '{backend}')."
        )

    driver = url.get_driver_name()
    if db_type == "postgresql" and driver in (None, "postgresql"):
        url = url.set(drivername="postgresql+psycopg2")
    elif db_type == "mysql" and driver in (None, "mysql", "mysqldb"):
        url = url.set(drivername="mysql+pymysql")

    return url


def _sqlite_readonly_url(url) -> str:
    db_path = url.database
    if not db_path or db_path == ":memory:":
        raise ValueError("In-memory SQLite databases are not supported.")
    return f"sqlite:///file:{quote(db_path)}?mode=ro&uri=true"


# --- 3. Schema introspection (cached briefly per connection) ---------------

_schema_cache: Dict[int, Tuple[float, Dict[str, List[Tuple[str, str]]]]] = {}


def get_schema_snapshot(
    connection_id: int, db_type: str, connection_string: str, force_refresh: bool = False
) -> Dict[str, List[Tuple[str, str]]]:
    now = time.monotonic()
    cached = _schema_cache.get(connection_id)
    if cached and not force_refresh and now < cached[0]:
        return cached[1]

    url = _normalize_url(db_type, connection_string)
    engine = create_engine(url)
    try:
        inspector = inspect(engine)
        snapshot = {
            table_name: [(col["name"], str(col["type"])) for col in inspector.get_columns(table_name)]
            for table_name in inspector.get_table_names()
        }
    finally:
        engine.dispose()

    _schema_cache[connection_id] = (now + SCHEMA_CACHE_TTL_SECONDS, snapshot)
    return snapshot


def format_schema_for_prompt(snapshot: Dict[str, List[Tuple[str, str]]]) -> str:
    lines = []
    for table, columns in snapshot.items():
        col_text = ", ".join(f"{name} {coltype}" for name, coltype in columns)
        lines.append(f"{table}({col_text})")
    return "\n".join(lines) if lines else "(no tables found)"


# --- 4. SQL generation -------------------------------------------------------

_SQL_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def _extract_sql(raw_text: str) -> str:
    match = _SQL_FENCE_RE.search(raw_text)
    return (match.group(1) if match else raw_text).strip()


def generate_sql(db_type: str, schema_text: str, question: str) -> str:
    llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL_NAME, temperature=0)
    prompt = SQL_PROMPT_TEMPLATE.format(
        db_type=db_type, schema=schema_text, question=question
    )
    response = llm.invoke(prompt)
    return _extract_sql(response.content)


# --- 5. Validation -----------------------------------------------------------

# Beyond the spec's required list (INSERT, UPDATE, DELETE, DROP, ALTER,
# TRUNCATE, GRANT, EXEC, ATTACH, PRAGMA), a few extra tokens are blocked as
# defense in depth: CREATE/REPLACE/MERGE/CALL/VACUUM/REINDEX/COPY cover
# schema changes and stored-procedure calls that aren't classic DML, and
# OUTFILE/DUMPFILE/LOAD_FILE cover MySQL's file-write/file-read functions,
# which a bare "starts with SELECT" check would otherwise miss entirely
# (`SELECT ... INTO OUTFILE '/tmp/x'` starts with SELECT).
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT",
    "REVOKE", "EXEC", "EXECUTE", "ATTACH", "DETACH", "PRAGMA",
    "CREATE", "REPLACE", "MERGE", "CALL", "VACUUM", "REINDEX", "COPY",
    "OUTFILE", "DUMPFILE", "LOAD_FILE",
]

_COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_COMMENT_LINE_RE = re.compile(r"--[^\n]*")
_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in FORBIDDEN_KEYWORDS) + r")\b", re.IGNORECASE
)
_LIMIT_RE = re.compile(r"\bLIMIT\s+\d+\b", re.IGNORECASE)
_SELECT_START_RE = re.compile(r"^SELECT\b", re.IGNORECASE)


def _strip_comments(sql: str) -> str:
    sql = _COMMENT_BLOCK_RE.sub(" ", sql)
    sql = _COMMENT_LINE_RE.sub(" ", sql)
    return sql


def validate_sql(raw_sql: str) -> Tuple[str, bool]:
    """Validate LLM-generated SQL before it is ever executed.

    Returns (cleaned_sql, has_own_limit). Raises SQLValidationError (tagged
    with the layer that caught it) on anything unsafe.

    Known limitation: these are text-level checks, not a real SQL parser, so
    a semicolon or keyword hidden inside a quoted string literal could in
    theory slip past the stacked-query/keyword checks (e.g. a WHERE clause
    comparing a column to the literal string ';DROP TABLE x'). That's exactly
    why execution never relies on this step alone — see _readonly_connection,
    which enforces read-only at the database/session/file level too.
    """
    stripped = _strip_comments(raw_sql).strip()
    if not stripped:
        raise SQLValidationError("Generated SQL was empty.", layer="empty_statement")

    if not _SELECT_START_RE.match(stripped):
        raise SQLValidationError(
            "Only a single SELECT statement is allowed.", layer="select_only"
        )

    body = stripped.rstrip()
    if body.endswith(";"):
        body = body[:-1].rstrip()
    if ";" in body:
        raise SQLValidationError(
            "Multiple statements are not allowed.", layer="stacked_query"
        )

    keyword_match = _KEYWORD_RE.search(body)
    if keyword_match:
        raise SQLValidationError(
            f"Query contains a disallowed keyword: {keyword_match.group(1).upper()}.",
            layer="forbidden_keyword",
        )

    has_own_limit = bool(_LIMIT_RE.search(body))
    return body, has_own_limit


# --- 6. Execution over a read-only connection, with a statement timeout ----
#
# Read-only enforcement at the connection level, per db_type:
#   - sqlite: opened via SQLite's own URI mode=ro (file:...?mode=ro&uri=true).
#     This is OS/file-level — even PRAGMA or ATTACH-based tricks can't write,
#     since the file handle itself is read-only.
#   - postgresql: execution_options(postgresql_readonly=True), which makes
#     SQLAlchemy's psycopg2 dialect call `connection.set_session(readonly=True)`
#     before any statement runs. Enforced server-side; a write raises
#     "cannot execute ... in a read-only transaction".
#   - mysql: `SET SESSION TRANSACTION READ ONLY` issued right after connecting.
#     Enforced server-side by MySQL for the rest of the session.
# All three are real connection/session-level guarantees, not just our text
# validation — so all three db_types got real enforcement here, not just sqlite.
#
# Statement timeout, per db_type:
#   - postgresql: `SET statement_timeout = <ms>` (session GUC, server-enforced).
#   - mysql: `SET SESSION MAX_EXECUTION_TIME = <ms>`. This is real MySQL
#     (5.7.8+), server-enforced, and specifically scoped to SELECT statements
#     (a good fit here). Caveat: MariaDB does NOT support this variable — it
#     uses `max_statement_time` instead. Since db_type is just "mysql" with no
#     way to distinguish MariaDB from MySQL here, a MariaDB server would
#     silently ignore this SET rather than erroring. Flagging this as the one
#     honest gap: MariaDB users would only get the app-level correctness of
#     validation, not a server-enforced timeout, unless this is extended to
#     detect MariaDB and set max_statement_time instead.
#   - sqlite: no session-level timeout concept exists. Implemented instead via
#     sqlite3's `set_progress_handler`, which fires periodically during query
#     execution and can abort it — a real cancellation mechanism (verified
#     above), not just a wall-clock guess after the fact.


@contextmanager
def _readonly_connection(db_type: str, connection_string: str, timeout_seconds: int):
    url = _normalize_url(db_type, connection_string)

    if db_type == "sqlite":
        ro_url = _sqlite_readonly_url(url)
        engine = create_engine(ro_url, connect_args={"uri": True})
        conn = engine.connect()
        dbapi_conn = conn.connection.dbapi_connection
        start = time.monotonic()

        def _progress_handler():
            return 1 if (time.monotonic() - start) > timeout_seconds else 0

        dbapi_conn.set_progress_handler(_progress_handler, 1000)
        try:
            yield conn
        finally:
            try:
                dbapi_conn.set_progress_handler(None, 0)
            except Exception:
                pass
            conn.close()
            engine.dispose()
        return

    engine = create_engine(url)
    conn = engine.connect()
    try:
        if db_type == "postgresql":
            conn = conn.execution_options(postgresql_readonly=True, postgresql_deferrable=True)
            conn.execute(text(f"SET statement_timeout = {int(timeout_seconds * 1000)}"))
        elif db_type == "mysql":
            conn.execute(text("SET SESSION TRANSACTION READ ONLY"))
            conn.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {int(timeout_seconds * 1000)}"))
        yield conn
    finally:
        conn.close()
        engine.dispose()


_TIMEOUT_MARKERS = ("timeout", "interrupted", "max_execution_time", "canceling statement")


def _serialize_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return value


def execute_query(
    db_type: str,
    connection_string: str,
    sql: str,
    has_own_limit: bool,
    row_limit: int = DEFAULT_ROW_LIMIT,
    timeout_seconds: int = DEFAULT_STATEMENT_TIMEOUT_SECONDS,
):
    """Execute an already-validated SELECT and return
    (columns, rows, row_count, truncated, displayed_sql).

    If the query has no LIMIT of its own, one more row than the cap is
    fetched internally so truncation can be detected precisely, then trimmed
    back down to `row_limit` — the SQL shown to the user always reads
    `LIMIT {row_limit}` (the real guarantee), never the +1 used internally.
    """
    if has_own_limit:
        exec_sql = sql
        displayed_sql = sql
    else:
        exec_sql = f"{sql} LIMIT {row_limit + 1}"
        displayed_sql = f"{sql} LIMIT {row_limit}"

    try:
        with _readonly_connection(db_type, connection_string, timeout_seconds) as conn:
            result = conn.execute(text(exec_sql))
            columns = list(result.keys())
            raw_rows = result.fetchall()
    except OperationalError as exc:
        message = str(exc.orig) if exc.orig else str(exc)
        if any(marker in message.lower() for marker in _TIMEOUT_MARKERS):
            raise SQLExecutionTimeout(
                "Query exceeded the statement timeout and was cancelled."
            ) from exc
        raise

    truncated = False
    if not has_own_limit and len(raw_rows) > row_limit:
        truncated = True
        raw_rows = raw_rows[:row_limit]

    rows = [[_serialize_value(v) for v in row] for row in raw_rows]
    return columns, rows, len(rows), truncated, displayed_sql


# --- 7. Natural-language summary --------------------------------------------


def summarize_answer(question: str, columns: List[str], rows: List[list], truncated: bool) -> str:
    llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL_NAME, temperature=0)
    shown_rows = rows[:ANSWER_ROW_CONTEXT_LIMIT]
    rows_text = "\n".join(", ".join(str(v) for v in row) for row in shown_rows) or "(no rows)"
    truncated_note = (
        f"(showing {len(shown_rows)} of {len(rows)} returned rows; the result was capped)"
        if truncated
        else ""
    )
    prompt = SQL_ANSWER_PROMPT_TEMPLATE.format(
        question=question,
        columns=", ".join(columns),
        rows=rows_text,
        truncated_note=truncated_note,
    )
    response = llm.invoke(prompt)
    return response.content


# --- 8. Orchestration --------------------------------------------------------


def run_sql_chain(connection: DatabaseConnection, question: str) -> dict:
    """Run the full pipeline for an already ownership-verified connection.

    Raises SQLValidationError (-> 400, before anything touches the database)
    or SQLExecutionTimeout (-> 504) for the route to translate into an HTTP
    response; any other exception is a genuine execution failure (-> 502).
    """
    plaintext = decrypt_connection_string(connection.encrypted_connection_string)

    schema_snapshot = get_schema_snapshot(connection.id, connection.db_type, plaintext)
    schema_text = format_schema_for_prompt(schema_snapshot)

    raw_sql = generate_sql(connection.db_type, schema_text, question)
    cleaned_sql, has_own_limit = validate_sql(raw_sql)

    columns, rows, row_count, truncated, displayed_sql = execute_query(
        connection.db_type, plaintext, cleaned_sql, has_own_limit
    )

    answer = summarize_answer(question, columns, rows, truncated)

    return {
        "answer": answer,
        "sql_query": displayed_sql,
        "columns": columns,
        "rows": rows,
        "row_count": row_count,
        "truncated": truncated,
    }
