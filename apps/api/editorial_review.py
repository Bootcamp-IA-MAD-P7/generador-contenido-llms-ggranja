"""Explicit human review boundary for generated editorial content."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from apps.api.drafting import EditableTextDraft
from apps.api.models import Platform


EditorialState = Literal[
    "generated_draft",
    "pending_human_review",
    "approved_final",
]
ReviewDecision = Literal["approve", "request_regeneration"]
RegenerationTrigger = Literal["human_feedback", "changed_inputs"]
ALLOWED_CHANGED_INPUTS = frozenset(
    {
        "topic_or_offer",
        "objective",
        "audience_context",
        "business_context_refs",
        "platforms",
        "format",
        "brand_and_constraints",
        "notes",
    }
)


class EditorialTransitionError(ValueError):
    """Raised when an editorial operation would violate the lifecycle."""


class HumanReview(BaseModel):
    """A human decision or feedback record for the current draft text."""

    decision: ReviewDecision
    feedback: str | None = Field(default=None, min_length=1)
    reviewer_ref: str | None = Field(default=None, min_length=1)
    reviewed_text_fingerprint: str = Field(min_length=1)


class RegenerationRequest(BaseModel):
    """Approved inputs for one #24.2 regeneration request."""

    trigger: RegenerationTrigger
    feedback: str | None = Field(default=None, min_length=1)
    changed_inputs: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_trigger_payload(self) -> "RegenerationRequest":
        unknown_inputs = set(self.changed_inputs) - ALLOWED_CHANGED_INPUTS
        if unknown_inputs:
            raise ValueError(
                "changed_inputs contains unsupported fields: "
                + ", ".join(sorted(unknown_inputs))
            )
        if self.trigger == "human_feedback":
            if not self.feedback or not self.feedback.strip():
                raise ValueError("human_feedback regeneration requires feedback")
            if self.changed_inputs:
                raise ValueError("human_feedback regeneration cannot change inputs")
        if self.trigger == "changed_inputs" and not self.changed_inputs:
            raise ValueError("changed_inputs regeneration requires changed inputs")
        return self


class EditorialLineage(BaseModel):
    """Minimal source link for a regenerated editorial item."""

    source_draft_id: str = Field(min_length=1)
    trigger: RegenerationTrigger
    feedback: str | None = Field(default=None, min_length=1)
    changed_inputs: dict[str, object] = Field(default_factory=dict)
    source_text_fingerprint: str = Field(min_length=1)


class EditorialContent(BaseModel):
    """Generated text plus its explicit editorial lifecycle state."""

    content_id: str = Field(min_length=1)
    state: EditorialState
    draft: EditableTextDraft
    owner_username: str | None = None
    brand_id: str | None = None
    business_id: str | None = None
    review: HumanReview | None = None
    lineage: EditorialLineage | None = None


class FinalTextArtifact(BaseModel):
    """Safe copy/export payload for an explicitly approved final text."""

    content_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    channel: Platform
    format: str = Field(min_length=1)


class EditorialReviewService:
    """Apply the Issue #24 editorial lifecycle and final text handoff."""

    @classmethod
    def from_generated_draft(
        cls,
        draft: EditableTextDraft,
        *,
        content_id: str,
        owner_username: str | None = None,
        brand_id: str | None = None,
        business_id: str | None = None,
    ) -> EditorialContent:
        """Wrap provider output as a generated, not-yet-reviewed item."""

        return EditorialContent(
            content_id=content_id,
            state="generated_draft",
            draft=draft,
            owner_username=owner_username,
            brand_id=brand_id,
            business_id=business_id,
        )

    @classmethod
    def submit_for_review(cls, content: EditorialContent) -> EditorialContent:
        """Move a generated draft into the explicit human-review state."""

        cls._require_state(content, "generated_draft", "submit for review")
        return content.model_copy(update={"state": "pending_human_review"})

    @classmethod
    def record_feedback(
        cls,
        content: EditorialContent,
        *,
        feedback: str,
        reviewer_ref: str | None = None,
    ) -> EditorialContent:
        """Record human feedback without regenerating or approving content."""

        cls._require_state(content, "pending_human_review", "record feedback")
        if not feedback.strip():
            raise EditorialTransitionError("feedback must contain meaningful text")
        review = HumanReview(
            decision="request_regeneration",
            feedback=feedback,
            reviewer_ref=reviewer_ref,
            reviewed_text_fingerprint=cls.text_fingerprint(content),
        )
        return content.model_copy(update={"review": review})

    @classmethod
    def approve(
        cls, content: EditorialContent, *, reviewer_ref: str
    ) -> EditorialContent:
        """Approve exactly the current text through an explicit human action."""

        cls._require_state(content, "pending_human_review", "approve")
        if not reviewer_ref.strip():
            raise EditorialTransitionError("reviewer_ref is required for approval")
        review = HumanReview(
            decision="approve",
            reviewer_ref=reviewer_ref,
            reviewed_text_fingerprint=cls.text_fingerprint(content),
        )
        return content.model_copy(update={"state": "approved_final", "review": review})

    @classmethod
    def manual_edit(
        cls,
        content: EditorialContent,
        *,
        caption: str,
        cta: str | None = None,
    ) -> EditorialContent:
        """Edit pending text without changing it into an approved final."""

        cls._require_state(content, "pending_human_review", "manual edit")
        if not caption.strip():
            raise EditorialTransitionError("caption must contain meaningful text")
        edited_draft = content.draft.model_copy(update={"caption": caption, "cta": cta})
        return content.model_copy(
            update={"draft": edited_draft, "review": None, "state": "pending_human_review"}
        )

    @classmethod
    def regenerate(
        cls,
        content: EditorialContent,
        request: RegenerationRequest,
        *,
        draft_factory: Callable[[EditorialContent, RegenerationRequest], EditableTextDraft],
    ) -> EditorialContent:
        """Create a new review-pending draft from feedback or allowed inputs."""

        cls._require_state(content, "pending_human_review", "regenerate")
        if request.trigger == "human_feedback":
            if content.review is None or content.review.decision != "request_regeneration":
                raise EditorialTransitionError(
                    "human_feedback regeneration requires recorded human feedback"
                )
            if request.feedback != content.review.feedback:
                raise EditorialTransitionError(
                    "regeneration feedback must match the recorded human feedback"
                )

        source_fingerprint = cls.text_fingerprint(content)
        try:
            generated_draft = draft_factory(content, request)
        except Exception as exc:  # noqa: BLE001 - preserve safe editorial state
            raise EditorialTransitionError("regeneration provider failed") from exc

        preserved_draft = generated_draft.model_copy(
            update={
                "evidence_refs": content.draft.evidence_refs,
                "assumptions": content.draft.assumptions,
                "review_notes": content.draft.review_notes,
                "evidence_provenance": content.draft.evidence_provenance,
                "supported_claims": content.draft.supported_claims,
                "unsupported_claims": content.draft.unsupported_claims,
            }
        )
        lineage = EditorialLineage(
            source_draft_id=content.content_id,
            trigger=request.trigger,
            feedback=request.feedback,
            changed_inputs=request.changed_inputs,
            source_text_fingerprint=source_fingerprint,
        )
        regenerated = cls.from_generated_draft(
            preserved_draft,
            content_id=f"{content.content_id}:regenerated:{uuid4().hex}",
            owner_username=content.owner_username,
            brand_id=content.brand_id,
            business_id=content.business_id,
        )
        return cls.submit_for_review(regenerated).model_copy(update={"lineage": lineage})

    @classmethod
    def copy_final(cls, content: EditorialContent) -> FinalTextArtifact:
        """Return only approved text and its channel/format metadata for copying."""

        return cls._final_text_artifact(content, "copy")

    @classmethod
    def export_final(cls, content: EditorialContent) -> FinalTextArtifact:
        """Return only approved text and its channel/format metadata for export."""

        return cls._final_text_artifact(content, "export")

    @classmethod
    def _final_text_artifact(
        cls, content: EditorialContent, operation: str
    ) -> FinalTextArtifact:
        cls._require_state(content, "approved_final", operation)
        return FinalTextArtifact(
            content_id=content.content_id,
            text=content.draft.caption,
            channel=content.draft.channel,
            format=content.draft.format,
        )

    @staticmethod
    def text_fingerprint(content: EditorialContent) -> str:
        """Return a stable fingerprint for the exact reviewable draft payload."""

        payload = content.draft.model_dump(mode="json")
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def _require_state(
        content: EditorialContent,
        expected: EditorialState,
        operation: str,
    ) -> None:
        if content.state != expected:
            raise EditorialTransitionError(
                f"cannot {operation} content in state {content.state!r}; "
                f"expected {expected!r}"
            )


__all__ = [
    "EditorialContent",
    "EditorialLineage",
    "EditorialReviewService",
    "EditorialState",
    "EditorialTransitionError",
    "FinalTextArtifact",
    "HumanReview",
    "RegenerationRequest",
]
