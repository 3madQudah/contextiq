"""
SQLAlchemy engine/session setup for the app's own database — SQLite locally
by default, PostgreSQL in production (e.g. Render), selected purely by what
DATABASE_URL is set to. No dialect-specific code should live outside this
module; api/dependencies.py and every model just import Base/get_db.

Provides the declarative Base and a get_db() dependency for FastAPI routes.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./contextiq.db")

# Some providers (Heroku historically, and anything copying that convention)
# hand out connection strings starting with "postgres://". SQLAlchemy 1.4+
# dropped that bare scheme name -- create_engine() raises
# NoSuchModuleError("Can't load plugin: sqlalchemy.dialects:postgres") on
# it -- so normalize it here rather than trip over that at deploy time.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# check_same_thread=False is required for SQLite when accessed across
# FastAPI's threaded request handlers; it's SQLite-specific and unrecognized
# (and unnecessary) by psycopg2, so it's only applied for sqlite:// URLs.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
