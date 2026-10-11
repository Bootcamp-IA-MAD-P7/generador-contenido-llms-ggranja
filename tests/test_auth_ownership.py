from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.auth import require_session
from apps.api.main import app, editorial_plan_store, editorial_store


client = TestClient(app)


class FakeGenerator:
    def generate(self, prompt: str) -> str:
        return "Borrador para el usuario autenticado."


def brief_payload() -> dict[str, object]:
    return {
        "topic_or_offer": "Oferta local",
        "objective": "Informar",
        "audience_context": "Personas del barrio",
        "business_context_refs": ["business-a"],
        "platforms": ["instagram"],
        "format": "single_image",
        "brand_and_constraints": "Claro",
        "facts": [],
    }


def use_user(username: str) -> None:
    app.dependency_overrides[require_session] = lambda: username


def test_new_draft_and_plan_are_scoped_to_the_authenticated_owner() -> None:
    editorial_store.clear()
    use_user("alice")
    with patch("apps.api.main.build_text_generator", return_value=FakeGenerator()):
        draft = client.post("/drafts", json={"brief": brief_payload()})
    assert draft.status_code == 200
    content_id = draft.json()["content_id"]
    owned_draft = client.get(f"/drafts/{content_id}")
    assert owned_draft.json()["owner_username"] == "alice"

    plan = {
        "strategy_id": "eighty_twenty",
        "strategy_version": "1.0.0",
        "total_slots": 1,
        "starts_on": "2026-10-01",
        "ends_on": "2026-10-31",
        "targets": {"VALUE": 1},
        "items": [{
            "source_ref": content_id,
            "source_kind": "editorial_content",
            "strategy_version": "1.0.0",
            "bucket_key": "VALUE",
            "platform": "instagram",
            "format": "single_image",
        }],
    }
    saved_plan = client.post("/plans", json=plan)
    assert saved_plan.status_code == 200
    plan_id = saved_plan.json()["plan_id"]
    assert saved_plan.json()["plan"]["owner_username"] == "alice"

    use_user("bob")
    assert client.get(f"/drafts/{content_id}").status_code == 404
    assert client.get(f"/drafts/{content_id}/review").status_code == 404
    assert client.patch(
        f"/drafts/{content_id}", json={"caption": "No autorizado"}
    ).status_code == 404
    assert client.get(f"/plans/{plan_id}").status_code == 404
    assert client.patch(
        f"/plans/{plan_id}/items/0/day", json={"day": "2026-10-15"}
    ).status_code == 404

    use_user("alice")
    assert client.get(f"/drafts/{content_id}").status_code == 200
    assert client.get(f"/plans/{plan_id}").status_code == 200

