"""
SQLAlchemy ORM models for chat history: Conversation and Message.

Kept in a separate module from auth/models.py (which is scoped to user
accounts) to avoid overloading that file's single responsibility, but still
inside the auth package since that's where the shared declarative Base
(auth.database.Base) already lives and every model needs it.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from auth.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(Base):
    """A per-user chat thread. Deleting it cascades to delete its messages."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    """A single turn in a conversation. role is "user" or "assistant"."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    conversation = relationship("Conversation", back_populates="messages")
