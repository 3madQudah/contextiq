"""
Auth endpoints: /register and /login. Issues JWT access tokens on success.
Both are rate-limited by IP (see utils/rate_limit.py) as a backstop
independent of anything the frontend does.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth.auth_handler import authenticate_user, register_user
from auth.database import get_db
from auth.jwt_handler import create_access_token
from auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from utils.rate_limit import limiter

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/15minutes")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/15minutes")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token)
