"""
Pydantic schemas for auth request/response payloads (register, login, token,
user output).
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from pydantic_core import PydanticCustomError

PASSWORD_MIN_LENGTH = 12
# Kept in sync with the frontend's PASSWORD_RULES (PasswordStrengthMeter.jsx)
# -- this is the real enforcement layer, that's the UX nicety.
PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-="
_SPECIAL_CHAR_RE = re.compile(r"[!@#$%^&*()_+\-=]")


def _password_requirement_failures(password: str) -> list[str]:
    failures = []
    if len(password) < PASSWORD_MIN_LENGTH:
        failures.append(f"at least {PASSWORD_MIN_LENGTH} characters")
    if not re.search(r"[A-Z]", password):
        failures.append("an uppercase letter")
    if not re.search(r"[a-z]", password):
        failures.append("a lowercase letter")
    if not re.search(r"\d", password):
        failures.append("a digit")
    if not _SPECIAL_CHAR_RE.search(password):
        failures.append(f"a special character ({PASSWORD_SPECIAL_CHARS})")
    return failures


class RegisterRequest(BaseModel):
    """Request body for registration: name, email, password."""

    first_name: str
    last_name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        failures = _password_requirement_failures(value)
        if failures:
            # PydanticCustomError (not a plain `raise ValueError(...)`) so the
            # resulting error's `msg` is exactly this string -- pydantic v2
            # prepends a "Value error, " prefix to plain ValueErrors, which
            # would otherwise leak into the message the frontend displays.
            raise PydanticCustomError(
                "password_too_weak",
                "Password must contain {failures}.",
                {"failures": ", ".join(failures)},
            )
        return value


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
