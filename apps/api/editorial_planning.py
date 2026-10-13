"""Deterministic, evidence-preserving editorial content-mix planning (#70).

Planning only: this module never generates, approves, schedules or publishes.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from apps.api.editorial_review import EditorialContent
from apps.api.models import GuidedBrief

Platform = Literal["instagram", "facebook"]
Format = Literal["single_image", "carousel", "reel"]


@dataclass(frozen=True)
class StrategyBucket:
    """One ordered bucket in an editorial strategy."""

    key: str
    label: str
    percentage: int

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key.strip():
            raise ValueError("bucket key cannot be empty")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("bucket label cannot be empty")
        if type(self.percentage) is not int or not 0 <= self.percentage <= 100:
            raise ValueError("bucket percentages must be integers between 0 and 100")


@dataclass(frozen=True)
class ContentMixStrategy:
    """Immutable, versioned strategy whose bucket order also resolves ties."""

    strategy_id: str
    version: str
    buckets: tuple[StrategyBucket, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.strategy_id, str) or not self.strategy_id.strip():
            raise ValueError("strategy_id cannot be empty")
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("version cannot be empty")
        if not isinstance(self.buckets, tuple) or not self.buckets:
            raise ValueError("buckets must be a non-empty tuple")
        if any(not isinstance(bucket, StrategyBucket) for bucket in self.buckets):
            raise ValueError("every bucket must be a StrategyBucket")
        keys = [bucket.key for bucket in self.buckets]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate bucket keys")
        if sum(bucket.percentage for bucket in self.buckets) != 100:
            raise ValueError("bucket percentages must sum to 100")

    def with_version(
        self, version: str, *, buckets: tuple[StrategyBucket, ...]
    ) -> "ContentMixStrategy":
        """Return a new immutable version without changing this strategy."""
        if version == self.version:
            raise ValueError("changed strategy requires a new version")
        return ContentMixStrategy(self.strategy_id, version, buckets)


EIGHTY_TWENTY = ContentMixStrategy(
    "eighty_twenty",
    "1.0.0",
    (
        StrategyBucket("VALUE", "Value and community", 80),
        StrategyBucket("PROMOTIONAL", "Promotion", 20),
    ),
)
THREE_THIRDS = ContentMixStrategy(
    "three_thirds",
    "1.0.0",
    (
        StrategyBucket("EDUCATIONAL", "Educational and informative", 34),
        StrategyBucket("COMMUNITY", "Interaction and community", 33),
        StrategyBucket("PROMOTIONAL", "Promotion and brand", 33),
    ),
)
PRESETS: Mapping[str, ContentMixStrategy] = MappingProxyType(
    {"eighty_twenty": EIGHTY_TWENTY, "three_thirds": THREE_THIRDS}
)


def allocate_slots(strategy: ContentMixStrategy, total: int) -> dict[str, int]:
    """Hamilton/largest remainder with stable declared-order tie breaking."""
    if not isinstance(strategy, ContentMixStrategy):
        raise TypeError("strategy must be a ContentMixStrategy")
    if type(total) is not int or total <= 0:
        raise ValueError("cycle size must be a positive integer")
    quotas = [total * bucket.percentage for bucket in strategy.buckets]
    counts = [quota // 100 for quota in quotas]
    remaining = total - sum(counts)
    order = sorted(
        range(len(quotas)),
        key=lambda index: (-(quotas[index] % 100), index),
    )
    for index in order[:remaining]:
        counts[index] += 1
    return {
        bucket.key: count for bucket, count in zip(strategy.buckets, counts)
    }


class PlannedItem(BaseModel):
    """Detached source metadata snapshot, not an edited source document."""

    model_config = ConfigDict(frozen=True)

    source_ref: str = Field(min_length=1)
    source_kind: Literal["guided_brief", "editorial_content"]
    strategy_version: str = Field(min_length=1)
    bucket_key: str = Field(min_length=1)
    platform: Platform
    format: Format
    scheduled_on: date | None = None
    review_state: str | None = None
    evidence: dict[str, object] = Field(default_factory=dict)

    @field_validator("source_ref", "strategy_version", "bucket_key")
    @classmethod
    def reject_blank_identifiers(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("identifier cannot be empty")
        return value


class EditorialPlan(BaseModel):
    """An allocated cycle and its current source references."""

    model_config = ConfigDict(frozen=True)

    strategy_id: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    total_slots: int = Field(gt=0, strict=True)
    starts_on: date
    ends_on: date
    targets: dict[str, int]
    owner_username: str | None = None
    items: tuple[PlannedItem, ...] = ()

    @field_validator("strategy_id", "strategy_version")
    @classmethod
    def reject_blank_strategy_identifiers(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("strategy identifiers cannot be empty")
        return value

    @field_validator("targets", mode="before")
    @classmethod
    def validate_targets(cls, value: object) -> object:
        if not isinstance(value, dict) or not value:
            raise ValueError("targets must be a non-empty bucket/count mapping")
        for key, count in value.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("target bucket keys cannot be empty")
            if type(count) is not int or count < 0:
                raise ValueError("target counts must be non-negative integers")
        return value

    @model_validator(mode="after")
    def validate_plan(self) -> "EditorialPlan":
        if self.ends_on < self.starts_on:
            raise ValueError("ends_on must not precede starts_on")
        if self.owner_username is not None and not self.owner_username.strip():
            raise ValueError("owner_username cannot be blank")
        if sum(self.targets.values()) != self.total_slots:
            raise ValueError("target counts must sum to total_slots")
        if len(self.items) > self.total_slots:
            raise ValueError("plan cannot exceed its cycle size")
        for item in self.items:
            if item.bucket_key not in self.targets:
                raise ValueError("planned item uses an unknown bucket key")
            if item.strategy_version != self.strategy_version:
                raise ValueError("planned item strategy version must match the plan")
            if item.scheduled_on is not None and not self.starts_on <= item.scheduled_on <= self.ends_on:
                raise ValueError("planned item day must be within the plan date range")
        return self

    def summary(self) -> dict[str, dict[str, int]]:
        actual = {key: 0 for key in self.targets}
        for item in self.items:
            actual[item.bucket_key] += 1
        return {
            key: {
                "target": target,
                "actual": actual[key],
                "difference": actual[key] - target,
            }
            for key, target in self.targets.items()
        }


def create_plan(
    strategy: ContentMixStrategy,
    total: int,
    *,
    starts_on: date,
    ends_on: date,
) -> EditorialPlan:
    """Allocate a dated planning cycle for one immutable strategy version."""
    return EditorialPlan(
        strategy_id=strategy.strategy_id,
        strategy_version=strategy.version,
        total_slots=total,
        starts_on=starts_on,
        ends_on=ends_on,
        targets=allocate_slots(strategy, total),
    )


def assign_item(
    plan: EditorialPlan,
    strategy: ContentMixStrategy,
    *,
    source: GuidedBrief | EditorialContent,
    source_ref: str,
    bucket_key: str,
    platform: str,
    format: str,
) -> EditorialPlan:
    """Attach a source snapshot without mutation or approval/publication actions."""
    if (plan.strategy_id, plan.strategy_version) != (
        strategy.strategy_id,
        strategy.version,
    ):
        raise ValueError("plan strategy version mismatch")
    if plan.targets != allocate_slots(strategy, plan.total_slots):
        raise ValueError("plan targets do not match the strategy allocation")
    if bucket_key not in plan.targets:
        raise ValueError("unknown bucket key")
    if platform not in ("instagram", "facebook") or format not in (
        "single_image",
        "carousel",
        "reel",
    ):
        raise ValueError("unsupported MVP platform or format")
    if not isinstance(source_ref, str) or not source_ref.strip():
        raise ValueError("source_ref is required")
    if len(plan.items) >= plan.total_slots:
        raise ValueError("plan cannot exceed its cycle size")

    if isinstance(source, EditorialContent):
        if platform != source.draft.channel or format != source.draft.format:
            raise ValueError("platform or format must match source draft")
        evidence = deepcopy(
            {
                "evidence_refs": source.draft.evidence_refs,
                "evidence_provenance": source.draft.evidence_provenance,
                "assumptions": source.draft.assumptions,
                "unsupported_claims": source.draft.unsupported_claims,
                "review_notes": source.draft.review_notes,
                "lineage": (
                    source.lineage.model_dump(mode="json") if source.lineage else None
                ),
            }
        )
        state = source.state
        kind = "editorial_content"
    elif isinstance(source, GuidedBrief):
        if platform not in source.platforms or format != source.format:
            raise ValueError("platform or format must match GuidedBrief")
        evidence = deepcopy(
            {
                "facts": [fact.model_dump(mode="json") for fact in source.facts],
                "business_context_refs": list(source.business_context_refs),
            }
        )
        state = None
        kind = "guided_brief"
    else:
        raise TypeError("source must be GuidedBrief or EditorialContent")

    item = PlannedItem(
        source_ref=source_ref,
        source_kind=kind,
        strategy_version=strategy.version,
        bucket_key=bucket_key,
        platform=platform,
        format=format,
        review_state=state,
        evidence=evidence,
    )
    return plan.model_copy(update={"items": (*plan.items, item)})


def reschedule_item(plan: EditorialPlan, item_index: int, scheduled_on: date) -> EditorialPlan:
    """Return a validated plan with one item's day changed inside the cycle range."""

    if type(item_index) is not int or item_index < 0 or item_index >= len(plan.items):
        raise IndexError("planned item index does not exist")
    if not plan.starts_on <= scheduled_on <= plan.ends_on:
        raise ValueError("planned item day must be within the plan date range")
    updated_items = list(plan.items)
    updated_items[item_index] = updated_items[item_index].model_copy(
        update={"scheduled_on": scheduled_on}
    )
    return EditorialPlan.model_validate(
        {**plan.model_dump(), "items": updated_items}
    )


__all__ = [
    "StrategyBucket",
    "ContentMixStrategy",
    "EIGHTY_TWENTY",
    "THREE_THIRDS",
    "PRESETS",
    "allocate_slots",
    "PlannedItem",
    "EditorialPlan",
    "create_plan",
    "assign_item",
    "reschedule_item",
]
