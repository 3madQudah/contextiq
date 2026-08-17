"""
Tests for auth endpoints: registration, login, and JWT token validation.

Passwords here must satisfy the strength validator in auth/schemas.py (see
tests/test_auth_security.py for edge cases on that, plus rate-limiting
coverage) -- that's the one requirement added since this file was first
written; registration is otherwise still immediate auto-login, no email
verification step.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.database import Base, get_db
from main import app
from utils.rate_limit import limiter

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_contextiq.db")
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

engine = create_engine(f"sqlite:///{TEST_DB_PATH}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)

STRONG_PASSWORD = "Str0ng!Passw0rd"


@pytest.fixture(autouse=True)
def _isolate_this_module():
    # Both this file and tests/test_auth_security.py hit the API through
    # the same `main.app`, so they share one app.dependency_overrides dict
    # and one rate limiter. Re-asserting our own db override per-test
    # (not just once at import time) means whichever module happened to
    # import last doesn't silently "win" the override for the other's
    # tests; resetting the limiter keeps one file's requests from eating
    # into the other's quota.
    app.dependency_overrides[get_db] = override_get_db
    limiter.reset()
    yield
    limiter.reset()


def test_register_user():
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "ada@example.com"
    assert "hashed_password" not in data


def test_register_duplicate_email_rejected():
    payload = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "dup@example.com",
        "password": STRONG_PASSWORD,
    }
    first = client.post("/api/auth/register", json=payload)
    second = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 400


def test_login_user():
    client.post(
        "/api/auth/register",
        json={
            "first_name": "Grace",
            "last_name": "Hopper",
            "email": "grace@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "grace@example.com", "password": STRONG_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_rejected():
    client.post(
        "/api/auth/register",
        json={
            "first_name": "Grace",
            "last_name": "Hopper",
            "email": "wrongpw@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "wrongpw@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
