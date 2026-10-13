"""Small SQLite persistence boundary for reviewable editorial content."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from apps.api.editorial_planning import EditorialPlan
from apps.api.editorial_review import EditorialContent


class EditorialContentStore:
    """Store validated editorial records in an isolated local SQLite database."""

    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        self._memory_connection = (
            sqlite3.connect(self._database_path) if self._database_path == ":memory:" else None
        )
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return self._memory_connection or sqlite3.connect(self._database_path)

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            if self._memory_connection is None:
                connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS editorial_content "
                "(content_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )

    def create(self, content: EditorialContent) -> EditorialContent:
        try:
            with self._connection() as connection:
                connection.execute(
                    "INSERT INTO editorial_content (content_id, payload) VALUES (?, ?)",
                    (content.content_id, content.model_dump_json()),
                )
        except sqlite3.IntegrityError as error:
            raise ValueError(f"content_id already exists: {content.content_id}") from error
        return content

    def create_id(self) -> str:
        return uuid4().hex

    def get(self, content_id: str, *, owner_username: str | None = None) -> EditorialContent | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload FROM editorial_content WHERE content_id = ?", (content_id,)
            ).fetchone()
        content = EditorialContent.model_validate_json(row[0]) if row else None
        if (
            content is not None
            and owner_username is not None
            and content.owner_username is not None
            and content.owner_username.casefold() != owner_username.casefold()
        ):
            return None
        return content

    def save(self, content: EditorialContent) -> EditorialContent:
        with self._connection() as connection:
            result = connection.execute(
                "UPDATE editorial_content SET payload = ? WHERE content_id = ?",
                (content.model_dump_json(), content.content_id),
            )
        if result.rowcount != 1:
            raise KeyError(content.content_id)
        return content

    def clear(self) -> None:
        with self._connection() as connection:
            connection.execute("DELETE FROM editorial_content")


class EditorialPlanStore:
    """Persist validated plans without owning strategy or lifecycle logic."""

    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        self._memory_connection = (
            sqlite3.connect(self._database_path) if self._database_path == ":memory:" else None
        )
        with self._connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS editorial_plan "
                "(plan_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return self._memory_connection or sqlite3.connect(self._database_path)

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            if self._memory_connection is None:
                connection.close()

    def create_id(self) -> str:
        return uuid4().hex

    def save(self, plan_id: str, plan: EditorialPlan) -> EditorialPlan:
        with self._connection() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO editorial_plan (plan_id, payload) VALUES (?, ?)",
                (plan_id, plan.model_dump_json()),
            )
        return plan

    def get(self, plan_id: str, *, owner_username: str | None = None) -> EditorialPlan | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload FROM editorial_plan WHERE plan_id = ?", (plan_id,)
            ).fetchone()
        plan = EditorialPlan.model_validate_json(row[0]) if row else None
        if (
            plan is not None
            and owner_username is not None
            and plan.owner_username is not None
            and plan.owner_username.casefold() != owner_username.casefold()
        ):
            return None
        return plan

    def list(self, *, owner_username: str | None = None) -> list[tuple[str, EditorialPlan]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT plan_id, payload FROM editorial_plan ORDER BY plan_id"
            ).fetchall()
        plans = [(plan_id, EditorialPlan.model_validate_json(payload)) for plan_id, payload in rows]
        if owner_username is None:
            return plans
        return [
            (plan_id, plan)
            for plan_id, plan in plans
            if plan.owner_username is None
            or plan.owner_username.casefold() == owner_username.casefold()
        ]


__all__ = ["EditorialContentStore", "EditorialPlanStore"]
