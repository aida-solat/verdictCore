"""Policy recommendation engine — suggest changes, never auto-apply."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from verdictcore.learning.analyzer import LearningPattern, LearningReport


class PolicyRecommendation(BaseModel):

    id: str
    policy_id: str | None = None
    recommendation_type: Literal[
        "adjust_weight",
        "add_constraint",
        "modify_constraint",
        "change_evidence_requirement",
        "require_review_rule",
    ]
    target: str
    current_value: Any = None
    suggested_value: Any = None
    confidence: float = 0.0
    reason: str = ""
    supporting_evidence: list[str] = []
    risk: Literal["low", "medium", "high"] = "medium"


class PolicyRecommender:

    def recommend(
        self,
        learning_report: LearningReport,
    ) -> list[PolicyRecommendation]:
        recommendations: list[PolicyRecommendation] = []

        for i, pattern in enumerate(learning_report.patterns):
            rec = self._pattern_to_recommendation(
                pattern, i, learning_report.policy_id,
            )
            if rec:
                recommendations.append(rec)

        return recommendations

    @staticmethod
    def _pattern_to_recommendation(
        pattern: LearningPattern,
        index: int,
        policy_id: str | None,
    ) -> PolicyRecommendation | None:
        rec_id = f"rec_{index:03d}"

        if pattern.pattern_type == "criterion_overestimation":
            return PolicyRecommendation(
                id=rec_id,
                policy_id=policy_id,
                recommendation_type="change_evidence_requirement",
                target=pattern.target,
                current_value="vendor_statement_allowed",
                suggested_value="third_party_or_contractual_required",
                confidence=pattern.confidence,
                reason=pattern.finding,
                risk="medium",
            )

        if pattern.pattern_type == "criterion_underperformance":
            return PolicyRecommendation(
                id=rec_id,
                policy_id=policy_id,
                recommendation_type="adjust_weight",
                target=pattern.target,
                current_value="current",
                suggested_value="increase",
                confidence=pattern.confidence,
                reason=pattern.finding,
                risk="medium",
            )

        return None
