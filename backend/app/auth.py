import hmac

from fastapi import Header, HTTPException

from app.config import settings


def require_auth(authorization: str = Header(...)) -> None:
    """Single static bearer token, single-user app (see DESIGN.md — this is
    a shared secret, not a full auth system; revisit if this ever becomes
    multi-user)."""
    token = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(token, settings.api_auth_token):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
