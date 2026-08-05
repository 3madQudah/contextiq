"""
SQLAlchemy ORM models for authentication (e.g. User table).
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from auth.database import Base


class User(Base):
    """User account: id, first/last name, email (unique), hashed_password, created_at."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # "Conversation" is defined in auth/chat_models.py — resolved by name against
    # the shared declarative Base registry, so no import-time circular dependency.
    conversations = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    # "DatabaseConnection" is defined in auth/db_connection_models.py, same reasoning.
    database_connections = relationship(
        "DatabaseConnection", back_populates="user", cascade="all, delete-orphan"
    )
