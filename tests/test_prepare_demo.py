from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from apps.api.auth import verify_password


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_demo.py"


def load_module():
    spec = importlib.util.spec_from_file_location("prepare_demo", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_env(path: Path) -> dict[str, str]:
    return {
        key: value
        for line in path.read_text(encoding="utf-8").splitlines()
        if "=" in line and not line.lstrip().startswith("#")
        for key, value in [line.split("=", 1)]
    }


def test_prepare_demo_writes_local_mock_configuration(tmp_path: Path) -> None:
    module = load_module()
    (tmp_path / ".env").write_text("GROQ_MODEL=kept-for-later\n", encoding="utf-8")

    module.prepare_demo(tmp_path)

    env = read_env(tmp_path / ".env")
    assert env["APP_ENV"] == "development"
    assert env["API_HOST"] == "127.0.0.1"
    assert env["API_PORT"] == "18000"
    assert env["NEXT_PUBLIC_API_BASE_URL"] == "http://127.0.0.1:18000"
    assert env["LLM_PROVIDER"] == "mock"
    assert env["AUTH_USERNAME"] == "gabriela"
    assert verify_password("gabriela", env["AUTH_PASSWORD_HASH"])
    assert env["GROQ_MODEL"] == "kept-for-later"
    assert "AUTH_PASSWORD" not in env
    assert (tmp_path / "apps/web/.env.local").read_text(encoding="utf-8") == (
        "NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:18000\n"
    )
    assert (tmp_path / ".local/credenciales-gabriela.txt").read_text(encoding="utf-8") == (
        "usuario: gabriela\ncontraseña: gabriela\n"
    )


def test_prepare_demo_refuses_non_development_environment(tmp_path: Path) -> None:
    module = load_module()
    (tmp_path / ".env").write_text("APP_ENV=production\n", encoding="utf-8")

    with pytest.raises(ValueError, match="APP_ENV"):
        module.prepare_demo(tmp_path)
