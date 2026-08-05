"""
Password hashing/verification and user authentication logic (passlib/bcrypt).
"""

from typing import Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from auth.models import User
from auth.schemas import RegisterRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def register_user(db: Session, payload: RegisterRequest) -> User:
    """Create a new user, raising ValueError if the email is already registered."""
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user is not None:
        raise ValueError("Email already registered")

    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Return the User if email/password match, else None."""
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
