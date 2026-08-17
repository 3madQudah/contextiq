"""
Tests for the security hardening added on top of registration/login:
password strength validation and rate limiting.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.database import Base, get_db
from main import app
from utils.rate_limit import limiter

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_auth_security.db")
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
    # Both this file and tests/test_auth.py hit the API through the same
    # `main.app`, so they share one app.dependency_overrides dict and one
    # rate limiter. Re-asserting our own db override per-test (not just
    # once at import time) means whichever module happened to import last
    # doesn't silently "win" the override for the other's tests;
    # resetting the limiter keeps one file's requests from eating into
    # the other's quota.
    app.dependency_overrides[get_db] = override_get_db
    limiter.reset()
    yield
    limiter.reset()


def _register(email, password=STRONG_PASSWORD, first_name="Ada", last_name="Lovelace"):
    return client.post(
        "/api/auth/register",
        json={"first_name": first_name, "last_name": last_name, "email": email, "password": password},
    )


# --- Password strength validation ------------------------------------------


def test_register_rejects_too_short_password():
    response = _register("short@example.com", password="Sh0rt!Aa")
    assert response.status_code == 422
    message = response.json()["detail"][0]["msg"]
    assert "12 characters" in message


def test_register_rejects_missing_uppercase():
    response = _register("noupper@example.com", password="all-lowercase-1!")
    assert response.status_code == 422
    assert "uppercase" in response.json()["detail"][0]["msg"]


def test_register_rejects_missing_digit():
    response = _register("nodigit@example.com", password="NoDigitsHere!!")
    assert response.status_code == 422
    assert "digit" in response.json()["detail"][0]["msg"]


def test_register_rejects_missing_special_char():
    response = _register("nospecial@example.com", password="NoSpecialChar123")
    assert response.status_code == 422
    assert "special character" in response.json()["detail"][0]["msg"]


def test_register_accepts_valid_password():
    response = _register("validpw@example.com")
    assert response.status_code == 201
    assert response.json()["email"] == "validpw@example.com"


# --- Rate limiting: register + login -----------------------------------------


def test_register_rate_limited_after_five_per_15_minutes():
    for i in range(5):
        response = _register(f"ratelimit{i}@example.com")
        assert response.status_code == 201

    sixth = _register("ratelimit-sixth@example.com")
    assert sixth.status_code == 429
    assert "detail" in sixth.json()


def test_login_rate_limited_after_five_per_15_minutes():
    _register("loginlimit@example.com")

    for _ in range(5):
        response = client.post(
            "/api/auth/login", json={"email": "loginlimit@example.com", "password": "wrong-password"}
        )
        assert response.status_code == 401

    sixth = client.post(
        "/api/auth/login", json={"email": "loginlimit@example.com", "password": "wrong-password"}
    )
    assert sixth.status_code == 429
    assert "detail" in sixth.json()
