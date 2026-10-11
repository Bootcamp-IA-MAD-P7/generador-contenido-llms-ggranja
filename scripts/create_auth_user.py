"""Create or rotate the local sign-in user.

Generates a random password, stores only its PBKDF2 hash and a signing secret in the
git-ignored ``.env``, and writes the plaintext password to the git-ignored
``.local/credenciales-<usuario>.txt``. The password is never printed.

Usage: python scripts/create_auth_user.py [usuario]
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.auth import hash_password  # noqa: E402

MANAGED = ("AUTH_USERNAME", "AUTH_PASSWORD_HASH", "AUTH_SECRET")


def main() -> None:
    username = (sys.argv[1] if len(sys.argv) > 1 else "gabriela").strip().lower()
    password = secrets.token_urlsafe(12)
    values = {
        "AUTH_USERNAME": username,
        "AUTH_PASSWORD_HASH": hash_password(password),
        "AUTH_SECRET": secrets.token_urlsafe(48),
    }

    env_path = ROOT / ".env"
    existing = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    kept = [line for line in existing if line.split("=", 1)[0].strip() not in MANAGED]
    kept.extend(f"{key}={value}" for key, value in values.items())
    env_path.write_text("\n".join(kept) + "\n", encoding="utf-8")

    credentials = ROOT / ".local" / f"credenciales-{username}.txt"
    credentials.parent.mkdir(exist_ok=True)
    credentials.write_text(f"usuario: {username}\ncontraseña: {password}\n", encoding="utf-8")
    print(f"Usuario '{username}' configurado. Credenciales en {credentials.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
