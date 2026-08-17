"""
FastAPI application entrypoint for ContextIQ.
Wires up the app instance, CORS, and mounts the auth/documents/chat routers.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth_routes import router as auth_router
from api.chat_routes import router as chat_router
from api.conversations_routes import router as conversations_router
from api.databases_routes import router as databases_router
from api.documents_routes import router as documents_router

# Importing models registers them on Base.metadata before create_all() runs below.
from auth import chat_models, db_connection_models, models  # noqa: F401
from auth.database import Base, engine
from utils.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

load_dotenv()

Base.metadata.create_all(bind=engine)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app = FastAPI(title="ContextIQ")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(conversations_router, prefix="/api/conversations", tags=["conversations"])
app.include_router(databases_router, prefix="/api/databases", tags=["databases"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
