"""
Shared slowapi rate limiter for the auth endpoints (register, login) —
brute-force/abuse protection independent of anything the frontend does,
since client-side checks alone are trivially bypassed.

Keyed by remote IP (slowapi's default `get_remote_address`): both endpoints
are unauthenticated, so IP is the only identifier available before a
request is ever validated.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# headers_enabled=False deliberately: slowapi's header injection on
# *successful* responses requires every decorated endpoint to declare a
# `response: Response` parameter for FastAPI to inject into (undocumented
# gotcha -- without it, slowapi raises trying to attach X-RateLimit-*
# headers to a plain dict/model return value). Not worth the coupling for
# headers that are a nicety; the 429 body's message is what actually
# matters here and doesn't depend on this.
limiter = Limiter(key_func=get_remote_address, headers_enabled=False)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Same {"detail": ...} shape as every other error response in this API
    (see api/*.py's HTTPExceptions) instead of slowapi's default {"error":
    ...} body, so the frontend's getErrorMessage() picks it up correctly."""
    return JSONResponse(
        {"detail": f"Too many attempts. Please try again later. (limit: {exc.detail})"},
        status_code=429,
    )
