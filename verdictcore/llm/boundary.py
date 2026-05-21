"""LLM boundary enforcement."""

from __future__ import annotations

from enum import Enum
from typing import Any

from verdictcore.models.result import DecisionResult


class LLMMode(str, Enum):

    STRICT = "strict"
    NARRATIVE_ONLY = "narrative_only"
    EVIDENCE_EXTRACTION = "evidence_extraction"


class LLMBoundary:

    def __init__(self, result: DecisionResult) -> None:
        self.result = result
        self._frozen_recommendation = result.recommendation.model_copy()
        self._frozen_rankings = [r.model_copy() for r in result.rankings]

    def get_context_for_narrative(self) -> dict[str, Any]:
        return {
            "decision_id": self.result.decision_id,
            "question": self.result.question,
            "status": self.result.status.value,
            "selected": self.result.recommendation.selected_alternative_name,
            "confidence": self.result.recommendation.confidence,
            "why_selected": self.result.explanation.why_selected,
            "top_drivers": [
                {"criterion": d.criterion, "impact": d.impact}
                for d in self.result.explanation.top_drivers
            ],
            "why_not": [
                {"alternative": wn.alternative_name, "reason": wn.reason}
                for wn in self.result.explanation.why_not
            ],
            "rankings": [
                {"name": r.name, "score": r.total_score, "blocked": r.blocked}
                for r in self.result.rankings
            ],
            "stability": (
                self.result.explanation.sensitivity.level
                if self.result.explanation.sensitivity
                else None
            ),
        }

    def verify_integrity(self) -> bool:
        return (
            self.result.recommendation == self._frozen_recommendation
            and len(self.result.rankings) == len(self._frozen_rankings)
            and all(
                r.alternative_id == f.alternative_id and r.total_score == f.total_score
                for r, f in zip(self.result.rankings, self._frozen_rankings)
            )
        )

    def generate_narrative(self, provider: str = "openai", mode: LLMMode = LLMMode.STRICT) -> str:
        context = self.get_context_for_narrative()
        parts: list[str] = []

        parts.append(f"Decision: {context['question']}")
        parts.append(f"Status: {context['status']}")

        if context["selected"]:
            parts.append(
                f"Recommendation: {context['selected']}"
                f" (confidence: {context['confidence']:.0%})"
            )

        parts.append(f"\n{context['why_selected']}")

        if context["why_not"]:
            parts.append("\nAlternatives considered:")
            for wn in context["why_not"]:
                parts.append(f"  - {wn['alternative']}: {wn['reason']}")

        if context["stability"]:
            parts.append(f"\nDecision stability: {context['stability']}")

        return "\n".join(parts)
