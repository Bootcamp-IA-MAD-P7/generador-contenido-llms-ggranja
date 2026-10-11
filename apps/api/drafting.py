"""Channel-adapted editable text drafting service."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import BaseModel, Field

from apps.api.copy_formulas import CopyApproach, approach_prompt_block, select_copy_approach
from apps.api.llm import TextGenerator
from apps.api.models import GuidedBrief, Platform
from apps.api.rag import LocalChromaIndex, RetrievedBusinessContext, ground_claim


@dataclass(frozen=True)
class TextTemplate:
    template_id: str
    version: str
    channel: Platform
    instructions: str


TEMPLATES: dict[Platform, TextTemplate] = {
    "instagram": TextTemplate(
        template_id="social.instagram.text-draft",
        version="1.0.0",
        channel="instagram",
        instructions=(
            "Use a concise hook, scannable caption, direct credible CTA and "
            "functional keywords only when grounded. Keep the draft concise, "
            "in Spanish by default or Catalan when configured; preserve source "
            "grounding and never invent prices, opening hours, promotions or dates."
        ),
    ),
    "facebook": TextTemplate(
        template_id="social.facebook.text-draft",
        version="1.0.0",
        channel="facebook",
        instructions=(
            "Use a conversational opening, enough context for the feed, a "
            "readable structure and a direct credible CTA. Keep it concise, "
            "in Spanish by default or Catalan when configured; preserve source "
            "grounding and never invent prices, opening hours, promotions or dates."
        ),
    ),
}


class EditableTextDraft(BaseModel):
    """Reviewable text output for one selected channel."""

    template_id: str
    template_version: str
    channel: Platform
    format: str
    caption: str = Field(min_length=1)
    cta: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    review_notes: list[str] = Field(default_factory=list)
    evidence_provenance: list[dict[str, object]] = Field(default_factory=list)
    supported_claims: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    copy_approach: str | None = None
    copy_formula: str | None = None
    approach_rationale: str | None = None


class ChannelAdaptedDraftService:
    """Select a versioned channel template and request one editable draft."""

    def __init__(self, generator: TextGenerator) -> None:
        self._generator = generator

    def draft(
        self,
        brief: GuidedBrief,
        *,
        retrieved_contexts: Sequence[RetrievedBusinessContext] = (),
        business_id: str | None = None,
        grounding_enabled: bool = False,
    ) -> list[EditableTextDraft]:
        """Return one grounded, editable text draft for every selected channel."""

        contexts = tuple(retrieved_contexts)
        if business_id is not None and any(
            context.business_id != business_id for context in contexts
        ):
            raise ValueError("retrieved context must match the requested business_id")
        return [
            self._draft_for_channel(brief, channel, contexts, grounding_enabled)
            for channel in brief.platforms
        ]

    def _draft_for_channel(
        self,
        brief: GuidedBrief,
        channel: Platform,
        retrieved_contexts: Sequence[RetrievedBusinessContext] = (),
        grounding_enabled: bool = False,
    ) -> EditableTextDraft:
        template = TEMPLATES[channel]
        supported_claims, unsupported_claims = _ground_brief_claims(
            brief, retrieved_contexts, grounding_enabled
        )
        selection = select_copy_approach(brief)
        prompt = self._build_prompt(
            brief,
            template,
            approach=selection[0] if selection else None,
            retrieved_contexts=retrieved_contexts,
            supported_claims=supported_claims,
            unsupported_claims=unsupported_claims,
            grounding_enabled=grounding_enabled,
        )
        generated_text = self._generator.generate(prompt).strip()
        if not generated_text:
            raise ValueError("text generator returned an empty draft")

        evidence_refs = (
            [context.text for context in retrieved_contexts]
            if grounding_enabled
            else [fact.statement for fact in brief.facts if fact.status == "CONFIRMED"]
        )
        assumptions = [
            fact.statement
            for fact in brief.facts
            if fact.status in {"INFERRED", "UNKNOWN"}
        ]
        review_notes = [
            "Review all inferred or unknown facts before approval.",
            "This draft is not a publication request.",
        ]
        if unsupported_claims:
            review_notes.append("Unsupported claims must not be presented as retrieved facts.")

        return EditableTextDraft(
            template_id=template.template_id,
            template_version=template.version,
            channel=channel,
            format=brief.format,
            caption=generated_text,
            evidence_refs=evidence_refs,
            assumptions=assumptions,
            review_notes=review_notes,
            evidence_provenance=[_provenance_dict(context) for context in retrieved_contexts],
            supported_claims=supported_claims,
            unsupported_claims=unsupported_claims,
            copy_approach=selection[0].label if selection else None,
            copy_formula=selection[0].formula if selection else None,
            approach_rationale=selection[1] if selection else None,
        )

    @staticmethod
    def _build_prompt(
        brief: GuidedBrief,
        template: TextTemplate,
        *,
        retrieved_contexts: Sequence[RetrievedBusinessContext] = (),
        supported_claims: Sequence[str] = (),
        unsupported_claims: Sequence[str] = (),
        grounding_enabled: bool = False,
        approach: CopyApproach | None = None,
    ) -> str:
        approach_block = f"{approach_prompt_block(approach)}\n" if approach else ""
        facts = "\n".join(
            f"- [{fact.status}] {fact.statement} (source: {fact.source}; "
            f"scope: {fact.scope})"
            for fact in brief.facts
        ) or "- No business facts supplied."

        retrieval = "\n".join(
            "- "
            f"[{context.source_type}] {context.text} "
            f"(source_id: {context.source_id}; version: {context.source_version}; "
            f"chunk_id: {context.chunk_id}; business_id: {context.business_id}; "
            f"source_file: {context.source_file or 'n/a'}; "
            f"page_number: {context.page_number or 'n/a'}; "
            f"source_uri: {context.source_uri or 'n/a'})"
            for context in retrieved_contexts
        ) or "- No retrieved business evidence."
        grounded_claims = "\n".join(f"- SUPPORTED: {claim}" for claim in supported_claims)
        rejected_claims = "\n".join(
            f"- UNSUPPORTED: {claim}" for claim in unsupported_claims
        ) or "- None"
        if not grounding_enabled:
            evidence_block = "Facts and evidence status:\n" + facts
        else:
            evidence_block = (
                "Retrieved evidence (the only business evidence allowed in this draft):\n"
                f"{retrieval}\n"
                "Claim grounding status:\n"
                f"{grounded_claims or '- No brief claims were supported.'}\n"
                f"{rejected_claims}"
            )
        return (
            f"Template: {template.template_id} v{template.version}\n"
            f"Channel: {template.channel}\n"
            f"Format: {brief.format}\n"
            f"Topic or offer: {brief.topic_or_offer or 'UNKNOWN'}\n"
            f"Objective: {brief.objective or 'UNKNOWN'}\n"
            f"Audience context: {brief.audience_context or 'UNKNOWN'}\n"
            f"Brand and constraints: {brief.brand_and_constraints or 'UNKNOWN'}\n"
            f"Channel instructions: {template.instructions}\n"
            f"{approach_block}"
            f"{evidence_block}\n"
            "Return only editable draft text. Never invent business facts, "
            "benefits, proof, deadlines, scarcity, credentials or guarantees. "
            "Keep historical dates and past events explicitly historical; do not "
            "present them as current facts unless the evidence says they are current. "
            "Keep inferred and unknown information out of factual claims. "
            "Do not render media, publish, schedule or request credentials."
        )


def _ground_brief_claims(
    brief: GuidedBrief,
    contexts: Sequence[RetrievedBusinessContext],
    grounding_enabled: bool,
) -> tuple[list[str], list[str]]:
    """Classify brief facts against retrieved evidence before generation."""

    supported: list[str] = []
    unsupported: list[str] = []
    for fact in brief.facts:
        if fact.status != "CONFIRMED":
            continue
        if not grounding_enabled:
            supported.append(fact.statement)
            continue
        result = ground_claim(fact.statement, contexts)
        (supported if result.supported else unsupported).append(fact.statement)
    return supported, unsupported


def _provenance_dict(context: RetrievedBusinessContext) -> dict[str, object]:
    return {
        "business_id": context.business_id,
        "source_type": context.source_type,
        "source_id": context.source_id,
        "source_version": context.source_version,
        "chunk_id": context.chunk_id,
        "source_file": context.source_file,
        "page_number": context.page_number,
        "source_uri": context.source_uri,
        "retrieved_at": context.retrieved_at,
        "source_sha256": context.source_sha256,
        "score": context.score,
    }


class RagGroundedDraftService:
    """Retrieve business evidence and pass only that evidence to drafting."""

    def __init__(self, index: LocalChromaIndex, generator: TextGenerator) -> None:
        self._index = index
        self._draft_service = ChannelAdaptedDraftService(generator)

    def draft(self, brief: GuidedBrief, *, business_id: str, top_k: int) -> list[EditableTextDraft]:
        query = self.build_query(brief)
        contexts = self._index.query(query, business_id, top_k)
        return self._draft_service.draft(
            brief,
            retrieved_contexts=contexts,
            business_id=business_id,
            grounding_enabled=True,
        )

    @staticmethod
    def build_query(brief: GuidedBrief) -> str:
        parts = [brief.topic_or_offer, brief.objective, brief.audience_context]
        query = " ".join(part for part in parts if part)
        if not query.strip():
            raise ValueError("brief must provide queryable topic, objective or audience")
        return query


__all__ = [
    "ChannelAdaptedDraftService",
    "EditableTextDraft",
    "RagGroundedDraftService",
    "TEMPLATES",
]
