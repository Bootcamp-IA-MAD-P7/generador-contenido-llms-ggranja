"""Prepare a deterministic, local-only configuration for the MVP demo.

This helper intentionally configures the offline mock provider and a loopback-only
API port.  It refuses non-development environments and writes only ignored local
configuration files; it never adds credentials to the repository.

Usage: python scripts/prepare_demo.py
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.auth import hash_password  # noqa: E402


DEMO_USERNAME = "gabriela"
DEMO_PASSWORD = "gabriela"
DEMO_PORT = 18000
DEMO_API_URL = f"http://127.0.0.1:{DEMO_PORT}"


def _key(line: str) -> str | None:
    key, separator, _ = line.partition("=")
    return key.strip() if separator and key.strip() and not key.lstrip().startswith("#") else None


def _read_values(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in lines:
        key = _key(line)
        if key is not None:
            values[key] = line.partition("=")[2].strip()
    return values


def _write_values(path: Path, values: dict[str, str]) -> None:
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    kept = [line for line in existing if _key(line) not in values]
    while kept and not kept[-1].strip():
        kept.pop()
    if kept:
        kept.append("")
    kept.extend(f"{key}={value}" for key, value in values.items())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")


def prepare_demo(root: Path = ROOT) -> None:
    """Write ignored local configuration for a deterministic offline demo."""

    env_path = root / ".env"
    current_lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    app_env = _read_values(current_lines).get("APP_ENV", "").strip().lower()
    if app_env and app_env != "development":
        raise ValueError("prepare_demo only runs when APP_ENV is development or unset")

    _write_values(
        env_path,
        {
            "APP_ENV": "development",
            "API_HOST": "127.0.0.1",
            "API_PORT": str(DEMO_PORT),
            "NEXT_PUBLIC_API_BASE_URL": DEMO_API_URL,
            "LLM_PROVIDER": "mock",
            "AUTH_USERNAME": DEMO_USERNAME,
            "AUTH_PASSWORD_HASH": hash_password(DEMO_PASSWORD),
            "AUTH_SECRET": secrets.token_urlsafe(48),
            "AUTH_REQUIRE_HTTPS": "false",
            "AUTH_TRUST_PROXY": "false",
        },
    )
    _write_values(
        root / "apps" / "web" / ".env.local",
        {"NEXT_PUBLIC_API_BASE_URL": DEMO_API_URL},
    )
    credentials = root / ".local" / "credenciales-gabriela.txt"
    credentials.parent.mkdir(parents=True, exist_ok=True)
    credentials.write_text(
        f"usuario: {DEMO_USERNAME}\ncontraseña: {DEMO_PASSWORD}\n",
        encoding="utf-8",
    )


def main() -> None:
    prepare_demo()
    print(
        "Demo local preparada: API en http://127.0.0.1:18000, "
        "proveedor mock y credenciales locales configuradas."
    )


if __name__ == "__main__":
    main()
