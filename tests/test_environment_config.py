from __future__ import annotations

import os
import socket
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from apps.api.config import (
    DEFAULT_API_BASE_URL,
    DEFAULT_API_HOST,
    DEFAULT_API_PORT,
    DEFAULT_APP_ENV,
    EnvironmentSettings,
)


ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = ROOT / ".env.example"


class EnvironmentConfigTests(unittest.TestCase):
    def test_defaults_are_safe_and_provider_free(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = EnvironmentSettings.from_environment()

        self.assertEqual(settings.app_env, DEFAULT_APP_ENV)
        self.assertEqual(settings.api_host, DEFAULT_API_HOST)
        self.assertEqual(settings.api_port, DEFAULT_API_PORT)
        self.assertEqual(settings.next_public_api_base_url, DEFAULT_API_BASE_URL)

    def test_environment_values_are_loaded_without_network_access(self) -> None:
        values = {
            "APP_ENV": "test",
            "API_HOST": "localhost",
            "API_PORT": "9000",
            "NEXT_PUBLIC_API_BASE_URL": "http://localhost:9000",
        }
        with patch.dict(os.environ, values, clear=True), patch.object(
            socket,
            "create_connection",
            side_effect=AssertionError("configuration must not use the network"),
        ):
            settings = EnvironmentSettings.from_environment()

        self.assertEqual(settings.api_port, 9000)
        self.assertEqual(settings.next_public_api_base_url, "http://localhost:9000")

    def test_invalid_values_fail_closed(self) -> None:
        with patch.dict(os.environ, {"API_PORT": "not-a-port"}, clear=True):
            with self.assertRaisesRegex(ValueError, "API_PORT"):
                EnvironmentSettings.from_environment()

        with patch.dict(
            os.environ,
            {"NEXT_PUBLIC_API_BASE_URL": "https://user:secret@example.test"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "credentials"):
                EnvironmentSettings.from_environment()

    def test_env_example_contains_only_non_secret_foundation_variables(self) -> None:
        content = ENV_EXAMPLE.read_text(encoding="utf-8")
        assignments = {
            line.split("=", 1)[0]
            for line in content.splitlines()
            if line and not line.startswith("#") and "=" in line
        }
        assignment_text = "\n".join(
            line for line in content.splitlines() if line and not line.startswith("#")
        )

        self.assertEqual(
            assignments,
            {
                "APP_ENV",
                "API_HOST",
                "API_PORT",
                "NEXT_PUBLIC_API_BASE_URL",
                "LLM_PROVIDER",
                "GROQ_API_KEY",
                "GROQ_MODEL",
                "OLLAMA_BASE_URL",
                "OLLAMA_MODEL",
                "LLM_TEMPERATURE",
                "LLM_TIMEOUT_SECONDS",
                "LLM_MAX_OUTPUT_TOKENS",
                "EDITORIAL_DATABASE_PATH",
                "RAG_EMBEDDING_MODEL",
                "RAG_EMBEDDING_REVISION",
                "RAG_CHROMA_COLLECTION",
                "RAG_CHROMA_PERSIST_DIRECTORY",
                "RAG_API_BASE_URL",
                "AUTH_USERNAME",
                "AUTH_PASSWORD_HASH",
                "AUTH_SECRET",
                "AUTH_TOKEN_TTL_MINUTES",
                "AUTH_USERS_JSON",
                "AUTH_LOGIN_MAX_ATTEMPTS",
                "AUTH_LOGIN_WINDOW_SECONDS",
                "AUTH_REQUIRE_HTTPS",
                "AUTH_TRUST_PROXY",
            },
        )
        self.assertRegex(assignment_text, r"(?m)^GROQ_API_KEY=$")
        self.assertNotRegex(assignment_text, r"(?i)(token|secret|password)=[^\\n]+\\S")
        self.assertNotRegex(assignment_text, r"(?i)(sk-[a-z0-9]|ghp_[a-z0-9]|ya29\.[a-z0-9])")

    def test_sensitive_env_files_are_ignored_but_example_is_trackable(self) -> None:
        for filename in (".env", ".env.local", ".env.production"):
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", "--quiet", filename],
                cwd=ROOT,
            )
            self.assertEqual(result.returncode, 0, filename)

        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", ".env.example"],
            cwd=ROOT,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_frontend_does_not_expose_backend_or_private_provider_configuration(self) -> None:
        source_paths = (
            ROOT / "apps" / "web" / "app" / "page.tsx",
            ROOT / "apps" / "web" / "components" / "Workspace.tsx",
            ROOT / "apps" / "web" / "components" / "shell" / "AppShell.tsx",
        )
        client = "\n".join(path.read_text(encoding="utf-8") for path in source_paths)

        self.assertIn("NEXT_PUBLIC_API_BASE_URL", client)
        self.assertNotRegex(client, r"(?i)(GROQ_API_KEY|GEMINI_API_KEY|GOOGLE_API_KEY|META_ACCESS_TOKEN)")


if __name__ == "__main__":
    unittest.main()
