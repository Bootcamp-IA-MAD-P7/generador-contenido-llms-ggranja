from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import date

from pydantic import ValidationError

from apps.api.drafting import EditableTextDraft
from apps.api.editorial_planning import (
    EIGHTY_TWENTY,
    PRESETS,
    THREE_THIRDS,
    ContentMixStrategy,
    EditorialPlan,
    PlannedItem,
    StrategyBucket,
    allocate_slots,
    assign_item,
    create_plan,
    reschedule_item,
)
from apps.api.editorial_review import (
    EditorialContent,
    EditorialLineage,
    EditorialReviewService,
    HumanReview,
)
from apps.api.models import GuidedBrief


START = date(2026, 10, 1)
END = date(2026, 10, 31)


def make_brief(platform: str = "instagram", format: str = "single_image") -> GuidedBrief:
    return GuidedBrief(
        topic_or_offer="Synthetic seasonal breakfast",
        objective="inform",
        audience_context="local customers",
        business_context_refs=["rag://synthetic/coll-amunt/menu-v1"],
        platforms=[platform],
        format=format,
        brand_and_constraints="Synthetic fixture; no real offer or customer data.",
        facts=[
            {
                "statement": "A seasonal breakfast option is available.",
                "status": "CONFIRMED",
                "source": "synthetic fixture",
                "reason": "provided for the test",
                "scope": "offer",
                "validation_needed": False,
            },
            {
                "statement": "It may appeal to nearby families.",
                "status": "INFERRED",
                "source": "test hypothesis",
                "reason": "synthetic audience hypothesis",
                "scope": "audience",
                "validation_needed": True,
            },
        ],
    )


def make_content(
    platform: str = "instagram",
    format: str = "single_image",
    state: str = "pending_human_review",
) -> EditorialContent:
    draft = EditableTextDraft(
        template_id=f"social.{platform}.text-draft",
        template_version="1.0.0",
        channel=platform,
        format=format,
        caption="Synthetic caption for a Coll Amunt! fixture.",
        evidence_refs=["synthetic:menu-v1#breakfast"],
        assumptions=["Synthetic audience assumption"],
        review_notes=["Check the current menu before approval."],
        evidence_provenance=[
            {
                "business_id": "synthetic-coll-amunt",
                "source_type": "pdf",
                "source_id": "synthetic-menu",
                "source_version": "1",
                "chunk_id": "synthetic-menu-1-p0001-c0001",
                "source_file": "synthetic-menu.pdf",
                "page_number": 1,
                "source_uri": None,
                "retrieved_at": None,
                "score": 0.1,
            }
        ],
        unsupported_claims=["Synthetic unsupported claim"],
    )
    review = None
    if state == "approved_final":
        review = HumanReview(
            decision="approve",
            reviewer_ref="synthetic-reviewer",
            reviewed_text_fingerprint="synthetic-fingerprint",
        )
    return EditorialContent(
        content_id="synthetic-content-1",
        state=state,
        draft=draft,
        review=review,
        lineage=EditorialLineage(
            source_draft_id="synthetic-source-draft",
            trigger="changed_inputs",
            changed_inputs={"objective": "inform"},
            source_text_fingerprint="synthetic-source-fingerprint",
        ),
    )


def make_plan(total: int = 10) -> EditorialPlan:
    return create_plan(EIGHTY_TWENTY, total, starts_on=START, ends_on=END)


class StrategyDefinitionTests(unittest.TestCase):
    def test_builtin_presets_have_canonical_order_and_versions(self) -> None:
        self.assertEqual(PRESETS["eighty_twenty"], EIGHTY_TWENTY)
        self.assertEqual(
            [(b.key, b.percentage) for b in EIGHTY_TWENTY.buckets],
            [("VALUE", 80), ("PROMOTIONAL", 20)],
        )
        self.assertEqual(
            [(b.key, b.percentage) for b in THREE_THIRDS.buckets],
            [
                ("EDUCATIONAL", 34),
                ("COMMUNITY", 33),
                ("PROMOTIONAL", 33),
            ],
        )
        self.assertEqual(EIGHTY_TWENTY.version, "1.0.0")
        self.assertEqual(THREE_THIRDS.version, "1.0.0")

    def test_strategy_and_preset_registry_are_immutable(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            EIGHTY_TWENTY.version = "2.0.0"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            EIGHTY_TWENTY.buckets[0].percentage = 1  # type: ignore[misc]
        with self.assertRaises(TypeError):
            PRESETS["custom"] = EIGHTY_TWENTY  # type: ignore[index]

    def test_valid_custom_mix_and_new_version_leave_old_version_unchanged(self) -> None:
        original = ContentMixStrategy(
            "local-test",
            "1.0.0",
            (
                StrategyBucket("STORY", "Useful story", 60),
                StrategyBucket("OFFER", "Offer", 40),
            ),
        )
        updated = original.with_version(
            "2.0.0",
            buckets=(
                StrategyBucket("STORY", "Useful story", 50),
                StrategyBucket("OFFER", "Offer", 50),
            ),
        )
        self.assertEqual(original.version, "1.0.0")
        self.assertEqual([b.percentage for b in original.buckets], [60, 40])
        self.assertEqual(updated.version, "2.0.0")
        self.assertEqual([b.percentage for b in updated.buckets], [50, 50])

    def test_rejects_invalid_bucket_keys_labels_and_percentages(self) -> None:
        invalid_buckets = (
            ("", "Label", 50),
            ("   ", "Label", 50),
            ("KEY", "", 50),
            ("KEY", "   ", 50),
            ("KEY", "Label", -1),
            ("KEY", "Label", 101),
            ("KEY", "Label", 12.5),
            ("KEY", "Label", True),
        )
        for args in invalid_buckets:
            with self.subTest(args=args), self.assertRaises(ValueError):
                StrategyBucket(*args)  # type: ignore[arg-type]

    def test_rejects_invalid_strategy_identity_shape_keys_and_totals(self) -> None:
        valid = (StrategyBucket("A", "A", 50), StrategyBucket("B", "B", 50))
        invalid = (
            ("", "1.0.0", valid),
            ("test", " ", valid),
            ("test", "1.0.0", ()),
            ("test", "1.0.0", [*valid]),
            (
                "test",
                "1.0.0",
                (StrategyBucket("A", "A", 50), StrategyBucket("A", "B", 50)),
            ),
            (
                "test",
                "1.0.0",
                (StrategyBucket("A", "A", 40), StrategyBucket("B", "B", 50)),
            ),
        )
        for args in invalid:
            with self.subTest(args=args), self.assertRaises(ValueError):
                ContentMixStrategy(*args)  # type: ignore[arg-type]

    def test_changed_strategy_cannot_reuse_same_version(self) -> None:
        with self.assertRaisesRegex(ValueError, "new version"):
            EIGHTY_TWENTY.with_version(
                EIGHTY_TWENTY.version, buckets=EIGHTY_TWENTY.buckets
            )


class AllocationTests(unittest.TestCase):
    def test_ten_post_preset_targets_match_contract(self) -> None:
        self.assertEqual(
            allocate_slots(EIGHTY_TWENTY, 10),
            {"VALUE": 8, "PROMOTIONAL": 2},
        )
        self.assertEqual(
            allocate_slots(THREE_THIRDS, 10),
            {"EDUCATIONAL": 4, "COMMUNITY": 3, "PROMOTIONAL": 3},
        )

    def test_allocation_sums_to_cycle_size_for_representative_sizes(self) -> None:
        for strategy in (EIGHTY_TWENTY, THREE_THIRDS):
            for total in (1, 3, 5, 10, 17):
                with self.subTest(strategy=strategy.strategy_id, total=total):
                    allocation = allocate_slots(strategy, total)
                    self.assertEqual(sum(allocation.values()), total)
                    self.assertEqual(allocation, allocate_slots(strategy, total))

    def test_equal_remainders_use_declared_bucket_order(self) -> None:
        strategy = ContentMixStrategy(
            "tie-test",
            "1.0.0",
            (
                StrategyBucket("FIRST", "First", 33),
                StrategyBucket("SECOND", "Second", 33),
                StrategyBucket("THIRD", "Third", 34),
            ),
        )
        self.assertEqual(
            allocate_slots(strategy, 2),
            {"FIRST": 1, "SECOND": 0, "THIRD": 1},
        )
        equal = ContentMixStrategy(
            "equal-test",
            "1.0.0",
            (
                StrategyBucket("FIRST", "First", 50),
                StrategyBucket("SECOND", "Second", 50),
            ),
        )
        self.assertEqual(
            allocate_slots(equal, 1),
            {"FIRST": 1, "SECOND": 0},
        )

    def test_rejects_invalid_cycle_sizes(self) -> None:
        for total in (0, -1, True, 1.5):
            with self.subTest(total=total), self.assertRaises(ValueError):
                allocate_slots(EIGHTY_TWENTY, total)  # type: ignore[arg-type]


class PlanTests(unittest.TestCase):
    def test_plan_dates_and_target_counts_are_validated(self) -> None:
        with self.assertRaises(ValidationError):
            create_plan(
                EIGHTY_TWENTY,
                3,
                starts_on=date(2026, 10, 3),
                ends_on=date(2026, 10, 2),
            )
        with self.assertRaises(ValidationError):
            EditorialPlan(
                strategy_id="eighty_twenty",
                strategy_version="1.0.0",
                total_slots=10,
                starts_on=START,
                ends_on=END,
                targets={"VALUE": 8, "PROMOTIONAL": 1},
            )
        with self.assertRaises(ValidationError):
            EditorialPlan(
                strategy_id="eighty_twenty",
                strategy_version="1.0.0",
                total_slots=1,
                starts_on=START,
                ends_on=END,
                targets={"VALUE": True, "PROMOTIONAL": 0},
            )

    def test_underfilled_plan_reports_target_actual_and_difference(self) -> None:
        plan = make_plan()
        actual = assign_item(
            plan,
            EIGHTY_TWENTY,
            source=make_brief(),
            source_ref="brief:synthetic-1",
            bucket_key="VALUE",
            platform="instagram",
            format="single_image",
        )
        self.assertEqual(
            actual.summary(),
            {
                "VALUE": {"target": 8, "actual": 1, "difference": -7},
                "PROMOTIONAL": {"target": 2, "actual": 0, "difference": -2},
            },
        )
        self.assertEqual(plan.items, ())

    def test_assignment_rejects_wrong_strategy_bucket_capacity_and_source_ref(self) -> None:
        plan = make_plan(total=1)
        brief = make_brief()
        cases = (
            {
                "strategy": THREE_THIRDS,
                "source": brief,
                "source_ref": "brief:1",
                "bucket_key": "EDUCATIONAL",
                "platform": "instagram",
                "format": "single_image",
            },
            {
                "strategy": EIGHTY_TWENTY,
                "source": brief,
                "source_ref": "brief:1",
                "bucket_key": "UNKNOWN",
                "platform": "instagram",
                "format": "single_image",
            },
            {
                "strategy": EIGHTY_TWENTY,
                "source": brief,
                "source_ref": "   ",
                "bucket_key": "VALUE",
                "platform": "instagram",
                "format": "single_image",
            },
        )
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                assign_item(plan, **kwargs)  # type: ignore[arg-type]
        full = assign_item(
            plan,
            EIGHTY_TWENTY,
            source=brief,
            source_ref="brief:1",
            bucket_key="VALUE",
            platform="instagram",
            format="single_image",
        )
        with self.assertRaisesRegex(ValueError, "cycle size"):
            assign_item(
                full,
                EIGHTY_TWENTY,
                source=brief,
                source_ref="brief:2",
                bucket_key="VALUE",
                platform="instagram",
                format="single_image",
            )


class SourcePreservationTests(unittest.TestCase):
    def test_guided_brief_matrix_covers_mvp_platforms_and_formats(self) -> None:
        for platform in ("instagram", "facebook"):
            for format in ("single_image", "carousel", "reel"):
                with self.subTest(platform=platform, format=format):
                    plan = create_plan(
                        EIGHTY_TWENTY, 1, starts_on=START, ends_on=END
                    )
                    brief = make_brief(platform, format)
                    before = brief.model_dump(mode="json")
                    result = assign_item(
                        plan,
                        EIGHTY_TWENTY,
                        source=brief,
                        source_ref=f"brief:synthetic:{platform}:{format}",
                        bucket_key="VALUE",
                        platform=platform,
                        format=format,
                    )
                    item = result.items[0]
                    self.assertEqual(item.source_kind, "guided_brief")
                    self.assertEqual(item.platform, platform)
                    self.assertEqual(item.format, format)
                    self.assertEqual(item.strategy_version, EIGHTY_TWENTY.version)
                    self.assertEqual(
                        item.evidence["facts"][1]["status"], "INFERRED"
                    )
                    self.assertEqual(
                        item.evidence["business_context_refs"],
                        ["rag://synthetic/coll-amunt/menu-v1"],
                    )
                    self.assertEqual(brief.model_dump(mode="json"), before)

    def test_editorial_content_preserves_state_lineage_evidence_and_source(self) -> None:
        source = make_content()
        before = source.model_dump(mode="json")
        plan = create_plan(EIGHTY_TWENTY, 1, starts_on=START, ends_on=END)
        result = assign_item(
            plan,
            EIGHTY_TWENTY,
            source=source,
            source_ref="content:synthetic-content-1",
            bucket_key="VALUE",
            platform="instagram",
            format="single_image",
        )
        item = result.items[0]
        self.assertEqual(item.source_kind, "editorial_content")
        self.assertEqual(item.review_state, "pending_human_review")
        self.assertEqual(item.evidence["evidence_refs"], ["synthetic:menu-v1#breakfast"])
        self.assertEqual(
            item.evidence["evidence_provenance"][0]["chunk_id"],
            "synthetic-menu-1-p0001-c0001",
        )
        self.assertEqual(item.evidence["assumptions"], ["Synthetic audience assumption"])
        self.assertEqual(
            item.evidence["unsupported_claims"], ["Synthetic unsupported claim"]
        )
        self.assertEqual(item.evidence["lineage"]["source_draft_id"], "synthetic-source-draft")
        self.assertEqual(source.model_dump(mode="json"), before)
        self.assertNotEqual(item.review_state, "approved_final")

        source.draft.evidence_refs.append("synthetic:later-edit")
        source.draft.evidence_provenance[0]["chunk_id"] = "mutated-source"
        self.assertEqual(item.evidence["evidence_refs"], ["synthetic:menu-v1#breakfast"])
        self.assertEqual(
            item.evidence["evidence_provenance"][0]["chunk_id"],
            "synthetic-menu-1-p0001-c0001",
        )

    def test_assignment_keeps_every_existing_review_state(self) -> None:
        for state in ("generated_draft", "pending_human_review", "approved_final"):
            with self.subTest(state=state):
                result = assign_item(
                    create_plan(EIGHTY_TWENTY, 1, starts_on=START, ends_on=END),
                    EIGHTY_TWENTY,
                    source=make_content(state=state),
                    source_ref=f"content:{state}",
                    bucket_key="VALUE",
                    platform="instagram",
                    format="single_image",
                )
                self.assertEqual(result.items[0].review_state, state)

    def test_rejects_unsupported_and_mismatched_targets_without_mutation(self) -> None:
        brief = make_brief()
        before = brief.model_dump(mode="json")
        invalid_targets = (
            ("linkedin", "single_image"),
            ("instagram", "story"),
            ("facebook", "single_image"),
        )
        for platform, format in invalid_targets:
            with self.subTest(platform=platform, format=format), self.assertRaises(
                ValueError
            ):
                assign_item(
                    make_plan(),
                    EIGHTY_TWENTY,
                    source=brief,
                    source_ref="brief:synthetic-1",
                    bucket_key="VALUE",
                    platform=platform,
                    format=format,
                )
        self.assertEqual(brief.model_dump(mode="json"), before)

    def test_editorial_source_cannot_be_assigned_to_a_different_channel_or_format(self) -> None:
        source = make_content()
        for platform, format in (("facebook", "single_image"), ("instagram", "reel")):
            with self.subTest(platform=platform, format=format), self.assertRaises(
                ValueError
            ):
                assign_item(
                    make_plan(),
                    EIGHTY_TWENTY,
                    source=source,
                    source_ref="content:synthetic-content-1",
                    bucket_key="VALUE",
                    platform=platform,
                    format=format,
                )
        self.assertEqual(source.state, "pending_human_review")


class PlannedItemDayTests(unittest.TestCase):
    def test_scheduled_day_is_preserved_and_must_be_within_plan_range(self) -> None:
        item = PlannedItem(
            source_ref="brief:synthetic-1",
            source_kind="guided_brief",
            strategy_version="1.0.0",
            bucket_key="VALUE",
            platform="instagram",
            format="single_image",
            scheduled_on=date(2026, 10, 3),
        )
        plan = EditorialPlan(
            strategy_id="eighty_twenty",
            strategy_version="1.0.0",
            total_slots=1,
            starts_on=START,
            ends_on=END,
            targets={"VALUE": 1},
            items=(item,),
        )
        moved = reschedule_item(plan, 0, date(2026, 10, 10))
        self.assertEqual(moved.items[0].scheduled_on, date(2026, 10, 10))
        self.assertEqual(plan.items[0].scheduled_on, date(2026, 10, 3))
        with self.assertRaisesRegex(ValueError, "within the plan date range"):
            reschedule_item(plan, 0, date(2026, 11, 1))
        with self.assertRaises(IndexError):
            reschedule_item(plan, 1, date(2026, 10, 10))

    def test_plan_rejects_scheduled_day_outside_cycle(self) -> None:
        with self.assertRaises(ValidationError):
            EditorialPlan(
                strategy_id="eighty_twenty",
                strategy_version="1.0.0",
                total_slots=1,
                starts_on=START,
                ends_on=END,
                targets={"VALUE": 1},
                items=(PlannedItem(
                    source_ref="brief:synthetic-1",
                    source_kind="guided_brief",
                    strategy_version="1.0.0",
                    bucket_key="VALUE",
                    platform="instagram",
                    format="single_image",
                    scheduled_on=date(2026, 11, 1),
                ),),
            )


if __name__ == "__main__":
    unittest.main()
