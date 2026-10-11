from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from apps.api.copy_formulas import approach_for_formula
from apps.api.main import app, editorial_store
from apps.api.models import GuidedBrief


client = TestClient(app)


class RecordingGenerator:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return f"Borrador {len(self.prompts)}"


def brief_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "topic_or_offer": "Aprender jugando",
        "objective": "Que conozcan la gamificación",
        "audience_context": "Responsables de equipos",
        "business_context_refs": ["talenthive"],
        "platforms": ["instagram"],
        "format": "single_image",
        "brand_and_constraints": "Cercano y profesional",
        "facts": [],
    }
    payload.update(overrides)
    return payload


@pytest.fixture(autouse=True)
def clear_editorial_store():
    editorial_store.clear()
    yield
    editorial_store.clear()


def create_reviewed_content(generator: RecordingGenerator, feedback: str) -> str:
    with patch("apps.api.main.build_text_generator", return_value=generator):
        created = client.post("/drafts", json={"brief": brief_payload()})
    assert created.status_code == 200
    content_id = created.json()["content_id"]
    recorded = client.post(
        f"/drafts/{content_id}/review",
        json={
            "decision": "request_regeneration",
            "reviewer_ref": "test-user",
            "feedback": feedback,
        },
    )
    assert recorded.status_code == 200
    return content_id


def regenerate(generator: RecordingGenerator, content_id: str, **body: object):
    with patch("apps.api.main.build_text_generator", return_value=generator):
        return client.post(
            f"/drafts/{content_id}/regenerate",
            json={"brief": brief_payload(), **body},
        )


def test_regeneration_uses_selected_formula_and_exact_recorded_feedback() -> None:
    generator = RecordingGenerator()
    feedback = "Haz más claro el valor para equipos pequeños."
    content_id = create_reviewed_content(generator, feedback)

    response = regenerate(generator, content_id, feedback=feedback, formula="PAS")

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "pending_human_review"
    assert body["content_id"] != content_id
    assert body["lineage"]["source_draft_id"] == content_id
    assert body["lineage"]["feedback"] == feedback
    assert body["draft"]["copy_formula"] == "PAS"
    assert "no tiene hechos confirmados" in body["draft"]["approach_rationale"]
    assert "optional scaffold: PAS" in generator.prompts[-1]
    assert feedback in generator.prompts[-1]


def test_regeneration_requires_matching_recorded_feedback_and_rejects_unknown_formula() -> None:
    generator = RecordingGenerator()
    content_id = create_reviewed_content(generator, "Aclarar el mensaje")

    mismatch = regenerate(generator, content_id, feedback="Otro feedback")
    assert mismatch.status_code == 409
    invalid = regenerate(generator, content_id, feedback="Aclarar el mensaje", formula="XYZ")
    assert invalid.status_code == 422


def test_regeneration_requires_a_recorded_feedback_decision() -> None:
    generator = RecordingGenerator()
    with patch("apps.api.main.build_text_generator", return_value=generator):
        created = client.post("/drafts", json={"brief": brief_payload()})
    content_id = created.json()["content_id"]
    response = regenerate(generator, content_id, feedback="Aclarar el mensaje")
    assert response.status_code == 409


def test_evidence_dependent_formula_warns_without_confirmed_facts() -> None:
    brief = GuidedBrief(**brief_payload())
    _, warning = approach_for_formula("4PS", brief)
    assert "no tiene hechos confirmados" in warning


def test_formula_does_not_warn_when_confirmed_facts_exist() -> None:
    brief = GuidedBrief(**brief_payload(facts=[{
        "statement": "El taller incluye una sesión de 30 minutos.",
        "status": "CONFIRMED",
        "source": "brief",
        "reason": "Supplied by the user",
        "scope": "offer",
        "validation_needed": False,
    }]))
    _, rationale = approach_for_formula("4PS", brief)
    assert "no tiene hechos confirmados" not in rationale
