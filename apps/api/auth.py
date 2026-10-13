"""Environment-backed authentication with bounded login attempts.

The local single-user variables remain supported for the prototype. A hosted
deployment can configure ``AUTH_USERS_JSON`` for multiple identities and require
HTTPS at the application boundary, including a deliberately opt-in trusted proxy
header. Credentials and signing secrets never leave the API process.
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
from threading import Lock
from typing import Final

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

PBKDF2_ITERATIONS = 240_000
DEFAULT_TOKEN_TTL_MINUTES = 480
DEFAULT_LOGIN_MAX_ATTEMPTS = 5
DEFAULT_LOGIN_WINDOW_SECONDS = 300


@dataclass(frozen=True)
class AuthUser:
    """One configured login identity."""

    username: str
    password_hash: str


@dataclass(frozen=True)
class AuthSettings:
    username: str
    password_hash: str
    secret: str
    token_ttl_minutes: int
    login_max_attempts: int = DEFAULT_LOGIN_MAX_ATTEMPTS
    login_window_seconds: int = DEFAULT_LOGIN_WINDOW_SECONDS
    require_https: bool = False
    trust_proxy: bool = False
    users: tuple[AuthUser, ...] = ()

    @property
    def configured_users(self) -> tuple[AuthUser, ...]:
        """Return configured users while preserving legacy single-user fields."""

        return self.users or (AuthUser(self.username, self.password_hash),)

    @classmethod
    def from_environment(cls) -> "AuthSettings | None":
        users_json = (os.getenv("AUTH_USERS_JSON") or "").strip()
        users: tuple[AuthUser, ...] = ()
        if users_json:
            try:
                parsed_users = json.loads(users_json)
            except (TypeError, ValueError):
                return None
            if not isinstance(parsed_users, dict) or not parsed_users:
                return None
            parsed: list[AuthUser] = []
            normalized_names: set[str] = set()
            for raw_username, raw_password_hash in parsed_users.items():
                if not isinstance(raw_username, str) or not isinstance(raw_password_hash, str):
                    return None
                username = raw_username.strip()
                password_hash = raw_password_hash.strip()
                normalized = username.casefold()
                if not username or not password_hash or normalized in normalized_names:
                    return None
                normalized_names.add(normalized)
                parsed.append(AuthUser(username, password_hash))
            users = tuple(parsed)

        username = (os.getenv("AUTH_USERNAME") or "").strip()
        password_hash = (os.getenv("AUTH_PASSWORD_HASH") or "").strip()
        if users:
            username = users[0].username
            password_hash = users[0].password_hash
        secret = (os.getenv("AUTH_SECRET") or "").strip()
        if not (username and password_hash and secret):
            return None

        def positive_int(name: str, default: int) -> int:
            try:
                value = int(os.getenv(name, str(default)))
            except ValueError:
                return default
            return max(value, 1)

        def env_flag(name: str, default: bool = False) -> bool:
            return (os.getenv(name, str(default)) or "").strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }

        try:
            ttl = int(os.getenv("AUTH_TOKEN_TTL_MINUTES", str(DEFAULT_TOKEN_TTL_MINUTES)))
        except ValueError:
            ttl = DEFAULT_TOKEN_TTL_MINUTES
        return cls(
            username,
            password_hash,
            secret,
            max(ttl, 1),
            login_max_attempts=positive_int(
                "AUTH_LOGIN_MAX_ATTEMPTS", DEFAULT_LOGIN_MAX_ATTEMPTS
            ),
            login_window_seconds=positive_int(
                "AUTH_LOGIN_WINDOW_SECONDS", DEFAULT_LOGIN_WINDOW_SECONDS
            ),
            require_https=env_flag("AUTH_REQUIRE_HTTPS"),
            trust_proxy=env_flag("AUTH_TRUST_PROXY"),
            users=users,
        )


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


def issue_token(
    settings: AuthSettings,
    *,
    now: float | None = None,
    username: str | None = None,
) -> tuple[str, int]:
    expires_at = int((now if now is not None else time.time()) + settings.token_ttl_minutes * 60)
    subject = (username or settings.username).strip()
    payload = _b64(json.dumps({"sub": subject, "exp": expires_at}, separators=(",", ":")).encode())
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


def resolve_username(settings: AuthSettings, username: str, password: str) -> str | None:
    """Return the canonical configured username for valid credentials."""

    normalized_username = username.strip().casefold().encode()
    matched: str | None = None
    for user in settings.configured_users:
        username_matches = hmac.compare_digest(
            normalized_username, user.username.casefold().encode()
        )
        password_matches = verify_password(password, user.password_hash)
        if username_matches and password_matches:
            matched = user.username
    return matched


def authenticate(settings: AuthSettings, username: str, password: str) -> bool:
    """Check credentials without exposing whether the username or password failed."""

    return resolve_username(settings, username, password) is not None


def is_configured_user(settings: AuthSettings, username: str) -> bool:
    """Return whether a token subject still belongs to the configured user set."""

    normalized = username.strip().casefold()
    return any(user.username.casefold() == normalized for user in settings.configured_users)


class LoginAttemptLimiter:
    """Small process-local sliding-window limiter for login attempts."""

    def __init__(self) -> None:
        self._attempts: dict[str, list[float]] = {}
        self._lock = Lock()

    def allow(self, key: str, *, max_attempts: int, window_seconds: int, now: float | None = None) -> bool:
        current = now if now is not None else time.monotonic()
        cutoff = current - window_seconds
        with self._lock:
            recent = [timestamp for timestamp in self._attempts.get(key, []) if timestamp > cutoff]
            if len(recent) >= max_attempts:
                self._attempts[key] = recent
                return False
            recent.append(current)
            self._attempts[key] = recent
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._attempts.clear()


login_attempt_limiter: Final = LoginAttemptLimiter()


_bearer = HTTPBearer(auto_error=False)


def request_uses_https(request: Request, settings: AuthSettings) -> bool:
    """Check direct HTTPS or an explicitly trusted proxy's forwarded scheme."""

    if request.url.scheme.lower() == "https":
        return True
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip().lower()
        return forwarded == "https"
    return False


def require_secure_transport(request: Request, settings: AuthSettings) -> None:
    if settings.require_https and not request_uses_https(request, settings):
        raise HTTPException(status_code=400, detail="HTTPS is required for authentication")


def login_attempt_key(request: Request, username: str) -> str:
    client_host = request.client.host if request.client else "unknown"
    return f"{client_host}:{username.strip().casefold()}"


def require_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """FastAPI dependency: the signed-in username, or 401."""

    settings = AuthSettings.from_environment()
    if settings is None:
        raise HTTPException(status_code=503, detail="authentication is not configured")
    require_secure_transport(request, settings)
    username = read_token(settings, credentials.credentials) if credentials else None
    if username is None or not is_configured_user(settings, username):
        raise HTTPException(
            status_code=401,
            detail="authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


__all__ = [
    "AuthUser",
    "AuthSettings",
    "authenticate",
    "hash_password",
    "is_configured_user",
    "issue_token",
    "login_attempt_key",
    "login_attempt_limiter",
    "read_token",
    "request_uses_https",
    "require_session",
    "require_secure_transport",
    "resolve_username",
    "verify_password",
]
