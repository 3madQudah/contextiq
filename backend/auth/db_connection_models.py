"""
SQLAlchemy ORM model for user-registered external SQL database connections
(text-to-SQL feature). Kept separate from auth/models.py and auth/chat_models.py
for the same reason those are split — single responsibility per module, all
sharing auth.database.Base.

The connection string is never stored in plaintext (see utils.crypto) and is
never included in any response schema — only ConnectionSummary (id, name,
db_type, created_at) leaves the API.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from auth.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DatabaseConnection(Base):
    """A user's saved external SQL database connection."""

    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    db_type = Column(String, nullable=False)  # "postgresql" | "mysql" | "sqlite"
    encrypted_connection_string = Column(String, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="database_connections")
