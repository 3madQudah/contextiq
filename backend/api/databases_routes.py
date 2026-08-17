"""
External database connection endpoints: register/list/delete a user's SQL
database connections, and ask natural-language questions about one
(text-to-SQL — see chain/sql_chain.py). Separate mechanism from the
file-based RAG chat: no embeddings, no retrieval, talks directly to the
user's own database.

Ownership enforcement mirrors api.conversations_routes: every route taking
{connection_id} depends on api.dependencies.get_owned_connection, so a stale
or foreign id always 404s.
"""

import logging
from datetime import datetime
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_owned_connection
from auth.database import get_db
from auth.db_connection_models import DatabaseConnection
from auth.models import User
from chain.sql_chain import (
    SQLConnectionError,
    SQLExecutionTimeout,
    SQLValidationError,
    run_sql_chain,
    test_connection,
)
from utils.crypto import encrypt_connection_string

logger = logging.getLogger(__name__)

router = APIRouter()

DBType = Literal["postgresql", "mysql", "sqlite"]


class ConnectionCreateRequest(BaseModel):
    name: str
    db_type: DBType
    connection_string: str


class ConnectionSummary(BaseModel):
    id: int
    name: str
    db_type: str
    created_at: datetime


class DBQueryRequest(BaseModel):
    question: str


class DBQueryResponse(BaseModel):
    answer: str
    sql_query: str
    columns: List[str]
    rows: List[list]
    row_count: int
    truncated: bool


def _to_summary(connection: DatabaseConnection) -> ConnectionSummary:
    return ConnectionSummary(
        id=connection.id,
        name=connection.name,
        db_type=connection.db_type,
        created_at=connection.created_at,
    )


@router.post("", response_model=ConnectionSummary, status_code=status.HTTP_201_CREATED)
def create_connection(
    payload: ConnectionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        test_connection(payload.db_type, payload.connection_string)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    connection = DatabaseConnection(
        user_id=current_user.id,
        name=payload.name,
        db_type=payload.db_type,
        encrypted_connection_string=encrypt_connection_string(payload.connection_string),
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return _to_summary(connection)


@router.get("", response_model=List[ConnectionSummary])
def list_connections(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    connections = (
        db.query(DatabaseConnection)
        .filter(DatabaseConnection.user_id == current_user.id)
        .order_by(DatabaseConnection.created_at.desc())
        .all()
    )
    return [_to_summary(c) for c in connections]


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection: DatabaseConnection = Depends(get_owned_connection),
    db: Session = Depends(get_db),
):
    db.delete(connection)
    db.commit()


@router.post("/{connection_id}/ask", response_model=DBQueryResponse)
def ask_database(
    payload: DBQueryRequest,
    connection: DatabaseConnection = Depends(get_owned_connection),
):
    try:
        result = run_sql_chain(connection, payload.question)
    except SQLValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Generated query was rejected ({exc.layer}): {exc}",
        )
    except SQLExecutionTimeout as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc))
    except SQLConnectionError as exc:
        # Distinct from the timeout above: this is the connection being
        # lost/refused (e.g. MySQL's "server has gone away" after an idle
        # period), not our own statement timeout firing on purpose. 503
        # ("try again shortly") reads more accurately to the caller than a
        # generic 502 -- already logged with the underlying driver error
        # inside chain/sql_chain.py at the point it was classified.
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        # Anything else is unclassified -- chain/sql_chain.run_sql_chain()
        # already logged it (with a stage-specific message: schema
        # introspection, Groq SQL generation, execution, or Groq
        # summarization) via logger.exception, so the traceback is in the
        # logs. Log again here too, at the route boundary, as a safety net
        # for the few steps in this file that aren't inside run_sql_chain
        # (e.g. a DBQueryResponse(**result) validation error would NOT land
        # here, since it happens outside this try block -- only run_sql_chain
        # failures do).
        logger.exception(
            "databases_routes: unclassified failure answering question "
            "(connection_id=%s, db_type=%s)",
            connection.id, connection.db_type,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to answer the question against this database.",
        ) from exc

    return DBQueryResponse(**result)
