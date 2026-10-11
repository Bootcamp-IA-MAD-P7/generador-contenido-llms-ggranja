from __future__ import annotations

import unittest
from unittest.mock import Mock

from apps.api.copy_formulas import approach_prompt_block, select_copy_approach
from apps.api.drafting import ChannelAdaptedDraftService
from apps.api.models import GuidedBrief

CONFIRMED_FACT = {
    "statement": "El diagnóstico dura 15 minutos y es gratuito",
    "status": "CONFIRMED",
    "source": "synthetic brief",
    "reason": "Explicitly supplied",
    "scope": "offer",
    "validation_needed": False,
}
UNKNOWN_FACT = {**CONFIRMED_FACT, "status": "UNKNOWN", "source": "none"}


def make_brief(objective: str | None, *, topic: str | None = "Tema", facts: list[dict] | None = None) -> GuidedBrief:
    return GuidedBrief(
        topic_or_offer=topic,
        objective=objective,
        audience_context="Vecinos del barrio",
        platforms=["instagram"],
        format="single_image",
        brand_and_constraints="claro y cercano",
        facts=facts or [],
    )


class CopyApproachSelectionTests(unittest.TestCase):
    def test_educational_objective_uses_four_cs_without_needing_facts(self) -> None:
        approach, reason = select_copy_approach(make_brief("Explicar qué es la gamificación"))  # type: ignore[misc]
        self.assertEqual((approach.key, approach.formula), ("educational", "4 Cs"))
        self.assertTrue(reason)

    def test_direct_response_prefers_four_ps_only_with_confirmed_proof(self) -> None:
        with_proof = select_copy_approach(make_brief("Que reserven una visita", facts=[CONFIRMED_FACT]))
        without_proof = select_copy_approach(make_brief("Que reserven una visita", facts=[UNKNOWN_FACT]))
        self.assertEqual(with_proof[0].formula, "4 Ps")  # type: ignore[index]
        self.assertEqual(without_proof[0].formula, "AIDA")  # type: ignore[index]

    def test_material_dependent_approaches_need_confirmed_facts(self) -> None:
        problem = "Mostrar la solución a un problema habitual"
        self.assertEqual(select_copy_approach(make_brief(problem, facts=[CONFIRMED_FACT]))[0].formula, "PAS")  # type: ignore[index]
        self.assertIsNone(select_copy_approach(make_brief(problem)))
        story = "Contar la experiencia de un cliente"
        self.assertEqual(select_copy_approach(make_brief(story, facts=[CONFIRMED_FACT]))[0].formula, "BAB")  # type: ignore[index]
        self.assertIsNone(select_copy_approach(make_brief(story)))

    def test_no_clear_signal_omits_the_formula(self) -> None:
        self.assertIsNone(select_copy_approach(make_brief("Mantener la presencia", topic="Novedades")))
        self.assertIsNone(select_copy_approach(make_brief(None, topic=None)))

    def test_prompt_block_is_a_guarded_optional_scaffold(self) -> None:
        approach = select_copy_approach(make_brief("Explicar qué es la gamificación"))[0]  # type: ignore[index]
        block = approach_prompt_block(approach)
        self.assertIn("optional scaffold: 4 Cs", block)
        self.assertIn("do not name the formula", block)
        self.assertIn("guaranteed performance", block)


class DraftingUsesApproachTests(unittest.TestCase):
    def test_draft_reports_and_prompts_the_selected_approach(self) -> None:
        generator = Mock()
        generator.generate.return_value = "Borrador editable"
        draft = ChannelAdaptedDraftService(generator).draft(make_brief("Explicar qué es la gamificación"))[0]
        self.assertEqual((draft.copy_approach, draft.copy_formula), ("Educativo", "4 Cs"))
        self.assertTrue(draft.approach_rationale)
        self.assertIn("Copy approach: Educativo", generator.generate.call_args.args[0])

    def test_without_signal_prompt_and_draft_are_unchanged(self) -> None:
        generator = Mock()
        generator.generate.return_value = "Borrador editable"
        draft = ChannelAdaptedDraftService(generator).draft(make_brief("Mantener la presencia", topic="Novedades"))[0]
        self.assertIsNone(draft.copy_approach)
        self.assertNotIn("Copy approach:", generator.generate.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
