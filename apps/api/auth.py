"""Local single-user authentication for the prototype (stdlib only).

Passwords are verified against a PBKDF2-HMAC-SHA256 hash held in the environment and
sessions are HMAC-signed, expiring bearer tokens. This is prototype-grade: no HTTPS
termination, rate limiting or multi-user management is provided.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

PBKDF2_ITERATIONS = 240_000
DEFAULT_TOKEN_TTL_MINUTES = 480


@dataclass(frozen=True)
class AuthSettings:
    username: str
    password_hash: str
    secret: str
    token_ttl_minutes: int

    @classmethod
    def from_environment(cls) -> "AuthSettings | None":
        username = (os.getenv("AUTH_USERNAME") or "").strip()
        password_hash = (os.getenv("AUTH_PASSWORD_HASH") or "").strip()
        secret = (os.getenv("AUTH_SECRET") or "").strip()
        if not (username and password_hash and secret):
            return None
        try:
            ttl = int(os.getenv("AUTH_TOKEN_TTL_MINUTES", str(DEFAULT_TOKEN_TTL_MINUTES)))
        except ValueError:
            ttl = DEFAULT_TOKEN_TTL_MINUTES
        return cls(username, password_hash, secret, max(ttl, 1))


def hash_password(password: str, *, salt: bytes | None = None, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = salt if salt is not None else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt_b64, digest_b64 = stored.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), base64.b64decode(salt_b64), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def issue_token(settings: AuthSettings, *, now: float | None = None) -> tuple[str, int]:
    expires_at = int((now if now is not None else time.time()) + settings.token_ttl_minutes * 60)
    payload = _b64(json.dumps({"sub": settings.username, "exp": expires_at}, separators=(",", ":")).encode())
    signature = _b64(hmac.new(settings.secret.encode(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}", expires_at


def read_token(settings: AuthSettings, token: str, *, now: float | None = None) -> str | None:
    """Return the username for a valid, unexpired token, else ``None``."""

    try:
        payload, signature = token.split(".")
        expected = _b64(hmac.new(settings.secret.encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(_unb64(payload))
        if int(data["exp"]) < (now if now is not None else time.time()):
            return None
        return str(data["sub"])
    except (ValueError, KeyError, TypeError):
        return None


def authenticate(settings: AuthSettings, username: str, password: str) -> bool:
    """Check both fields in constant time so a wrong user and a wrong password look alike."""

    user_ok = hmac.compare_digest(username.strip().lower().encode(), settings.username.lower().encode())
    password_ok = verify_password(password, settings.password_hash)
    return user_ok and password_ok


_bearer = HTTPBearer(auto_error=False)


def require_session(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    """FastAPI dependency: the signed-in username, or 401."""

    settings = AuthSettings.from_environment()
    if settings is None:
        raise HTTPException(status_code=503, detail="authentication is not configured")
    username = read_token(settings, credentials.credentials) if credentials else None
    if username is None:
        raise HTTPException(
            status_code=401,
            detail="authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


__all__ = [
    "AuthSettings",
    "authenticate",
    "hash_password",
    "issue_token",
    "read_token",
    "require_session",
    "verify_password",
]
