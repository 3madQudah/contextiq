"""
Tests for chain/sql_chain.py's OperationalError classification: recognizing
our own configured statement timeout firing (SQLExecutionTimeout) versus the
MySQL connection being lost/refused out from under us (SQLConnectionError),
versus anything unrecognized passing through unchanged.

These are the fix for the intermittent-502 issue on MySQL connections: before
this, a MySQL "server has gone away"/"lost connection" error didn't match any
of the (Postgres/SQLite-flavored) timeout marker strings, so it fell through
to a bare `raise` and surfaced as an opaque, unlogged 502 indistinguishable
from any other failure. No network access or real database is used here --
OperationalError instances are constructed directly with fake DBAPI-shaped
`.orig` exceptions matching what PyMySQL/psycopg2/sqlite3 actually produce.
"""

import pytest
from sqlalchemy.exc import OperationalError

from chain.sql_chain import (
    SQLConnectionError,
    SQLExecutionTimeout,
    _classify_operational_error,
    _mysql_errno,
    execute_query,
)


def _operational_error(errno, message):
    """Build an OperationalError whose `.orig` looks like a real DBAPI
    exception: `.args = (errno, message)`, same shape PyMySQL/psycopg2 use."""

    class _FakeDBAPIError(Exception):
        pass

    orig = _FakeDBAPIError(errno, message) if errno is not None else _FakeDBAPIError(message)
    return OperationalError("SELECT 1", {}, orig)


# ---------------------------------------------------------------------------
# _mysql_errno
# ---------------------------------------------------------------------------


def test_mysql_errno_extracted_from_orig_args():
    exc = _operational_error(2006, "(2006, 'MySQL server has gone away')")
    assert _mysql_errno(exc) == 2006


def test_mysql_errno_none_when_first_arg_not_int():
    exc = _operational_error(None, "some non-numeric-prefixed error")
    assert _mysql_errno(exc) is None


# ---------------------------------------------------------------------------
# _classify_operational_error -- MySQL connection-lost cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "errno,message",
    [
        (2006, "MySQL server has gone away"),
        (2013, "Lost connection to MySQL server during query"),
        (2003, "Can't connect to MySQL server on 'host' (110)"),
        (4031, "The client was disconnected by the server because of inactivity"),
    ],
)
def test_mysql_connection_lost_by_errno(errno, message):
    exc = _operational_error(errno, message)
    result = _classify_operational_error("mysql", exc)
    assert isinstance(result, SQLConnectionError)


def test_mysql_connection_lost_by_message_when_errno_unavailable():
    """Some drivers/wrappers won't shape .orig.args as (errno, msg) -- the
    message-text fallback must still catch the common phrasings."""
    exc = _operational_error(None, "MySQL server has gone away")
    assert _mysql_errno(exc) is None  # confirms this is exercising the fallback path
    result = _classify_operational_error("mysql", exc)
    assert isinstance(result, SQLConnectionError)


def test_mysql_connection_lost_is_mysql_only():
    """The same message text must NOT trigger SQLConnectionError for
    Postgres/SQLite -- this is a MySQL-client-protocol-specific signature,
    not a generic phrase to match against any backend."""
    exc = _operational_error(None, "server has gone away")
    result = _classify_operational_error("postgresql", exc)
    assert result is exc
    result = _classify_operational_error("sqlite", exc)
    assert result is exc


# ---------------------------------------------------------------------------
# _classify_operational_error -- our own configured timeout firing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "db_type,message",
    [
        ("postgresql", "canceling statement due to statement timeout"),
        ("mysql", "Query execution was interrupted, max_execution_time exceeded"),
        ("sqlite", "interrupted"),
    ],
)
def test_own_timeout_recognized_per_db_type(db_type, message):
    exc = _operational_error(None, message)
    result = _classify_operational_error(db_type, exc)
    assert isinstance(result, SQLExecutionTimeout)


def test_mysql_timeout_not_misclassified_as_connection_lost():
    """A MySQL MAX_EXECUTION_TIME timeout and a MySQL connection drop must
    not collide -- the timeout is us cancelling a slow query on purpose (504),
    not the connection failing (503), even though both are MySQL errors."""
    exc = _operational_error(3024, "Query execution was interrupted, max_execution_time exceeded")
    result = _classify_operational_error("mysql", exc)
    assert isinstance(result, SQLExecutionTimeout)
    assert not isinstance(result, SQLConnectionError)


# ---------------------------------------------------------------------------
# _classify_operational_error -- unrecognized errors pass through unchanged
# ---------------------------------------------------------------------------


def test_unrecognized_mysql_error_passes_through_unchanged():
    exc = _operational_error(1146, "Table 'medicheck.patients' doesn't exist")
    result = _classify_operational_error("mysql", exc)
    assert result is exc


# ---------------------------------------------------------------------------
# execute_query wiring: the classifier's result actually gets raised
# ---------------------------------------------------------------------------


def test_execute_query_raises_sqlconnectionerror_on_mysql_gone_away(monkeypatch):
    """`_readonly_connection` is a plain callable from execute_query's point of
    view -- `with _readonly_connection(...) as conn:` calls it, then enters the
    result. Raising directly inside the replacement (rather than yielding) means
    the exception surfaces at that call, before `__enter__` is ever reached --
    no need to fake the @contextmanager machinery to exercise this path."""
    from chain import sql_chain

    def _raise_gone_away(db_type, connection_string, timeout_seconds):
        raise _operational_error(2006, "MySQL server has gone away")

    monkeypatch.setattr(sql_chain, "_readonly_connection", _raise_gone_away)

    with pytest.raises(SQLConnectionError):
        execute_query("mysql", "mysql://fake", "SELECT 1", has_own_limit=True)


def test_execute_query_raises_sqlexecutiontimeout_on_configured_timeout(monkeypatch):
    from chain import sql_chain

    def _raise_timeout(db_type, connection_string, timeout_seconds):
        raise _operational_error(None, "canceling statement due to statement timeout")

    monkeypatch.setattr(sql_chain, "_readonly_connection", _raise_timeout)

    with pytest.raises(SQLExecutionTimeout):
        execute_query("postgresql", "postgresql://fake", "SELECT 1", has_own_limit=True)


def test_execute_query_reraises_unrecognized_operational_error(monkeypatch):
    from chain import sql_chain

    def _raise_unrecognized(db_type, connection_string, timeout_seconds):
        raise _operational_error(1146, "Table 'medicheck.patients' doesn't exist")

    monkeypatch.setattr(sql_chain, "_readonly_connection", _raise_unrecognized)

    with pytest.raises(OperationalError):
        execute_query("mysql", "mysql://fake", "SELECT 1", has_own_limit=True)
