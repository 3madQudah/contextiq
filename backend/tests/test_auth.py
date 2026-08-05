"""
Tests for auth endpoints: registration, login, and JWT token validation.
"""

import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.database import Base, get_db
from main import app

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


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_register_user():
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "password": "supersecret",
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
        "password": "supersecret",
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
            "password": "supersecret",
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "grace@example.com", "password": "supersecret"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_rejected():
    response = client.post(
        "/api/auth/login",
        json={"email": "grace@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
