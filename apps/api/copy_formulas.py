"""Deterministic copy-approach and formula selection (expert-content-generation).

Implements the approach/formula table of
``openspec/changes/expert-content-generation/design.md`` as an optional, explainable
scaffold. Formulas guide structure only: they never add facts, never promise
performance and are not required to be named in the final text. When no signal in the
brief clearly supports an approach, nothing is selected and the draft falls back to the
channel template alone.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from apps.api.models import GuidedBrief


@dataclass(frozen=True)
class CopyApproach:
    key: str
    label: str
    formula: str
    structure: str
    safeguard: str


_DIRECT = CopyApproach(
    key="direct_response",
    label="Respuesta directa",
    formula="AIDA",
    structure="Attention, Interest, Desire, Action: one hook, one supported benefit, one reason to act now, one proportionate CTA.",
    safeguard="State only benefits supported by confirmed facts; use a CTA proportionate to the offer.",
)
_DIRECT_PROOF = CopyApproach(
    key="direct_response",
    label="Respuesta directa",
    formula="4 Ps",
    structure="Picture, Promise, Proof, Push: paint the situation, state the supported promise, give the confirmed proof, close with a clear CTA.",
    safeguard="Proof must come from confirmed facts or retrieved evidence; never invent proof or guarantees.",
)
_NARRATIVE = CopyApproach(
    key="narrative",
    label="Narrativo",
    formula="BAB",
    structure="Before, After, Bridge: the real starting situation, the supported improved state, and how the business connects them.",
    safeguard="Use only supplied experiences; do not invent a story, emotion or outcome.",
)
_EDUCATIONAL = CopyApproach(
    key="educational",
    label="Educativo",
    formula="4 Cs",
    structure="Clear, Concise, Credible, Convincing: one idea explained plainly, short, backed by what is confirmed.",
    safeguard="Distinguish expertise from credentials or results that have not been confirmed.",
)
_DISRUPTIVE = CopyApproach(
    key="disruptive",
    label="Disruptivo o entretenido",
    formula="Bucle abierto",
    structure="Open loop: raise a question or curiosity in the hook and resolve it within the content.",
    safeguard="Avoid humiliation, stereotypes and unsupported shock; do not obscure the message.",
)
_PROBLEM = CopyApproach(
    key="problem_solution",
    label="Problema y solución",
    formula="PAS",
    structure="Problem, Agitation, Solution: name the real problem, acknowledge its weight without exaggerating, present the supported solution.",
    safeguard="Agitation must not exaggerate harm; testimony, offer and response sections require evidence.",
)

_SIGNALS: list[tuple[str, tuple[str, ...]]] = [
    ("problem", ("problema", "dolor", "solucion", "evitar", "error", "problem", "pain point")),
    ("narrative", ("experiencia", "historia", "testimonio", "cliente", "transform", "antes y despues", "story", "testimonial")),
    ("educational", ("explic", "educ", "aprend", "que es", "como funciona", "consejo", "autoridad", "confianza", "informar", "inform", "tips")),
    ("direct", ("vender", "venta", "promo", "oferta", "reserv", "compra", "visita", "inscri", "pedir", "solicit", "conocer", "descubr", "request", "buy", "book")),
    ("disruptive", ("humor", "divertid", "sorpren", "curiosidad", "entreten", "viral")),
]


def _normalise(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return re.sub(r"\s+", " ", "".join(ch for ch in decomposed if not unicodedata.combining(ch)))


def select_copy_approach(brief: GuidedBrief) -> tuple[CopyApproach, str] | None:
    """Return the suggested approach and a human-editable reason, or ``None``.

    Only the objective and topic drive the choice. Approaches that require real
    material (problem/solution, narrative, proof-based direct response) are chosen only
    when the brief carries at least one CONFIRMED fact.
    """

    text = _normalise(f"{brief.objective or ''} {brief.topic_or_offer or ''}")
    if not text.strip():
        return None
    has_confirmed = any(fact.status == "CONFIRMED" for fact in brief.facts)
    matched = {name for name, stems in _SIGNALS if any(stem in text for stem in stems)}

    if "problem" in matched and has_confirmed:
        return _PROBLEM, "El objetivo apunta a un problema y su solución, y el brief aporta hechos confirmados."
    if "narrative" in matched and has_confirmed:
        return _NARRATIVE, "El objetivo busca conectar con una experiencia real y el brief aporta hechos confirmados."
    if "educational" in matched:
        return _EDUCATIONAL, "El objetivo es explicar o generar confianza, así que prima la claridad y la credibilidad."
    if "direct" in matched:
        if has_confirmed:
            return _DIRECT_PROOF, "El objetivo busca una respuesta y hay hechos confirmados que sirven de prueba."
        return _DIRECT, "El objetivo busca una respuesta; sin hechos confirmados se usa una progresión simple hacia la acción."
    if "disruptive" in matched:
        return _DISRUPTIVE, "El objetivo pide llamar la atención con curiosidad o entretenimiento."
    return None


def approach_prompt_block(approach: CopyApproach) -> str:
    """Prompt guidance: an optional scaffold, never a source of facts."""

    return (
        f"Copy approach: {approach.label} (optional scaffold: {approach.formula}).\n"
        f"Scaffold: {approach.structure}\n"
        f"Safeguard: {approach.safeguard}\n"
        "Use the scaffold only if it improves the message; do not force it, do not "
        "name the formula in the text and do not imply guaranteed performance."
    )


__all__ = ["CopyApproach", "approach_prompt_block", "select_copy_approach"]
