"""
Pydantic schemas for auth request/response payloads (register, login, token, user output).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class RegisterRequest(BaseModel):
    """Request body for registration: name, email, password."""

    first_name: str
    last_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Request body for login: email + password."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Response body representing a user, without password fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    """Response body for issued JWT access tokens."""

    access_token: str
    token_type: str = "bearer"
