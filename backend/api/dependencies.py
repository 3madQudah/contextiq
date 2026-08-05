"""
Shared FastAPI dependencies: resolves the current authenticated user from the
JWT bearer token in the Authorization header, and enforces conversation
ownership so a stale/foreign id always 404s instead of leaking existence.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth.chat_models import Conversation
from auth.database import get_db
from auth.db_connection_models import DatabaseConnection
from auth.jwt_handler import decode_access_token
from auth.models import User

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user


def get_owned_conversation_by_id(
    db: Session, user_id: int, conversation_id: int
) -> Conversation:
    """Fetch a conversation the given user owns, or raise 404.

    Single source of truth for the ownership check: a conversation that
    doesn't exist and a conversation owned by someone else are indistinguishable
    to the caller — both 404. Used both as the plain helper below (for routes
    where conversation_id arrives in the request body, e.g. /api/chat/ask) and
    wrapped as a path-parameter dependency by get_owned_conversation.
    """
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return conversation


def get_owned_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Conversation:
    """FastAPI dependency for routes with {conversation_id} in the path."""
    return get_owned_conversation_by_id(db, current_user.id, conversation_id)


def get_owned_connection_by_id(
    db: Session, user_id: int, connection_id: int
) -> DatabaseConnection:
    """Fetch a database connection the given user owns, or raise 404.

    Same rationale as get_owned_conversation_by_id: a connection that doesn't
    exist and one owned by someone else must be indistinguishable to the
    caller, so both cases 404 rather than 403 (which would confirm the id
    belongs to someone).
    """
    connection = (
        db.query(DatabaseConnection)
        .filter(DatabaseConnection.id == connection_id, DatabaseConnection.user_id == user_id)
        .first()
    )
    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Database connection not found"
        )
    return connection


def get_owned_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DatabaseConnection:
    """FastAPI dependency for routes with {connection_id} in the path."""
    return get_owned_connection_by_id(db, current_user.id, connection_id)
