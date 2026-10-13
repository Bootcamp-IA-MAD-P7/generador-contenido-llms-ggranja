import json
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from apps.api.auth import (
    AuthSettings,
    hash_password,
    issue_token,
    login_attempt_limiter,
    read_token,
    require_session,
    verify_password,
)
from apps.api.main import app

client = TestClient(app)
PASSWORD = "correct horse battery"


@pytest.fixture(autouse=True)
def real_auth():
    app.dependency_overrides.pop(require_session, None)
    login_attempt_limiter.clear()
    env = {
        "AUTH_USERNAME": "gabriela",
        "AUTH_PASSWORD_HASH": hash_password(PASSWORD, iterations=1_000),
        "AUTH_SECRET": "test-secret-only",
        "AUTH_LOGIN_MAX_ATTEMPTS": "5",
        "AUTH_LOGIN_WINDOW_SECONDS": "300",
        "AUTH_REQUIRE_HTTPS": "false",
        "AUTH_TRUST_PROXY": "false",
    }
    with patch.dict(os.environ, env, clear=False):
        os.environ.pop("AUTH_USERS_JSON", None)
        yield
    login_attempt_limiter.clear()


def login(username: str = "gabriela", password: str = PASSWORD):
    return client.post("/auth/login", json={"username": username, "password": password})


def test_password_hash_verifies_only_the_right_password() -> None:
    stored = hash_password("one", iterations=1_000)
    assert verify_password("one", stored)
    assert not verify_password("two", stored)
    assert not verify_password("one", "not-a-hash")
    assert "one" not in stored


def test_login_returns_a_token_that_opens_protected_routes() -> None:
    response = login()
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "gabriela"
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.get("/auth/me", headers=headers).json() == {"username": "gabriela"}
    assert client.get("/plans", headers=headers).status_code == 200


def test_username_is_case_insensitive_but_wrong_credentials_are_rejected_alike() -> None:
    assert login(username="Gabriela").status_code == 200
    wrong_password = login(password="nope")
    wrong_user = login(username="otra")
    assert wrong_password.status_code == wrong_user.status_code == 401
    assert wrong_password.json() == wrong_user.json()


def test_protected_routes_need_a_valid_session_but_readiness_stays_open() -> None:
    assert client.get("/readiness").status_code == 200
    for method, path in [
        ("get", "/plans"),
        ("get", "/drafts/x"),
        ("post", "/drafts"),
        ("post", "/drafts/x/regenerate"),
        ("get", "/auth/me"),
    ]:
        assert getattr(client, method)(path).status_code == 401, path
    assert client.patch(
        "/plans/plan-x/items/0/day", json={"day": "2026-10-15"}
    ).status_code == 401
    assert client.get("/plans", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_tokens_expire_and_cannot_be_forged() -> None:
    settings = AuthSettings("gabriela", "h", "secret", 1)
    token, _ = issue_token(settings, now=1_000)
    assert read_token(settings, token, now=1_030) == "gabriela"
    assert read_token(settings, token, now=1_000 + 61) is None
    payload, signature = token.split(".")
    assert read_token(settings, f"{payload}.{signature[:-2]}xx", now=1_030) is None
    other = AuthSettings("gabriela", "h", "other-secret", 1)
    assert read_token(other, token, now=1_030) is None


def test_unconfigured_authentication_fails_closed() -> None:
    with patch.dict(os.environ, {"AUTH_SECRET": ""}, clear=False):
        assert login().status_code == 503
        assert client.get("/plans").status_code == 503


def test_login_attempts_are_limited_and_success_resets_the_window() -> None:
    with patch.dict(
        os.environ,
        {"AUTH_LOGIN_MAX_ATTEMPTS": "2", "AUTH_LOGIN_WINDOW_SECONDS": "300"},
    ):
        assert login(password="wrong").status_code == 401
        assert login(password="wrong").status_code == 401
        blocked = login(password="wrong")
        assert blocked.status_code == 429
        assert blocked.headers["retry-after"] == "300"

        login_attempt_limiter.clear()
        assert login(password=PASSWORD).status_code == 200
        assert login(password="wrong").status_code == 401


def test_multiple_configured_users_receive_canonical_session_identity() -> None:
    second_password = "second user password"
    users = {
        "gabriela": hash_password(PASSWORD, iterations=1_000),
        "marina": hash_password(second_password, iterations=1_000),
    }
    with patch.dict(os.environ, {"AUTH_USERS_JSON": json.dumps(users)}):
        response = login(username="MARINA", password=second_password)
        assert response.status_code == 200
        body = response.json()
        assert body["username"] == "marina"
        headers = {"Authorization": f"Bearer {body['access_token']}"}
        assert client.get("/auth/me", headers=headers).json() == {"username": "marina"}


def test_https_requirement_accepts_direct_or_trusted_proxy_https_only() -> None:
    with patch.dict(os.environ, {"AUTH_REQUIRE_HTTPS": "true"}):
        assert login().status_code == 400
        https_client = TestClient(app, base_url="https://testserver")
        response = https_client.post(
            "/auth/login",
            json={"username": "gabriela", "password": PASSWORD},
        )
        assert response.status_code == 200

    with patch.dict(
        os.environ,
        {"AUTH_REQUIRE_HTTPS": "true", "AUTH_TRUST_PROXY": "true"},
    ):
        response = client.post(
            "/auth/login",
            json={"username": "gabriela", "password": PASSWORD},
            headers={"X-Forwarded-Proto": "https"},
        )
        assert response.status_code == 200
