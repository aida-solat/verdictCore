"""Decision result schema and output types."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class DecisionStatus(str, Enum):

    DECIDED = "decided"
    BLOCKED = "blocked"
    NEEDS_REVIEW = "needs_review"
    INSUFFICIENT_DATA = "insufficient_data"
    ERROR = "error"


class Recommendation(BaseModel):

    selected_alternative_id: str | None = None
    selected_alternative_name: str | None = None
    decision_class: Literal["approve", "reject", "escalate", "no_selection"] = "approve"
    confidence: float = Field(ge=0.0, le=1.0)


class CriterionTrace(BaseModel):

    raw: float | int | None = None
    normalized: float | None = None
    weight: float
    weighted: float | None = None


class CalculationTrace(BaseModel):

    alternative_id: str
    alternative_name: str
    criteria: dict[str, CriterionTrace] = {}
    total_score: float = 0.0


class RankedAlternative(BaseModel):

    alternative_id: str
    name: str
    rank: int | None = None
    total_score: float
    blocked: bool = False
    warnings: list[str] = []
    calculation_trace: CalculationTrace | None = None


class ConstraintResult(BaseModel):

    alternative_id: str
    alternative_name: str
    field: str
    operator: str
    required_value: Any
    actual_value: Any
    action: str
    passed: bool
    message: str | None = None


class TopDriver(BaseModel):

    criterion: str
    impact: float


class WhyNot(BaseModel):

    alternative_id: str
    alternative_name: str
    reason: str


class SensitivityResult(BaseModel):

    decision_stability_score: float = Field(ge=0.0, le=1.0)
    level: Literal["stable", "moderately_stable", "fragile", "unstable"]
    sensitive_to: list[str] = []
    winner_changes_if: list[dict[str, Any]] = []


class Explanation(BaseModel):

    why_selected: str
    top_drivers: list[TopDriver] = []
    why_not: list[WhyNot] = []
    sensitivity: SensitivityResult | None = None


class AuditSummary(BaseModel):

    engine_version: str
    policy_version: str
    input_hash: str
    ruleset_hash: str
    output_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DecisionResult(BaseModel):

    decision_id: str
    domain: str
    question: str
    status: DecisionStatus
    recommendation: Recommendation
    rankings: list[RankedAlternative] = []
    constraint_results: list[ConstraintResult] = []
    explanation: Explanation
    audit: AuditSummary
    warnings: list[str] = []
    metadata: dict[str, Any] = {}

    @property
    def selected(self) -> RankedAlternative | None:
        if self.recommendation.selected_alternative_id:
            for r in self.rankings:
                if r.alternative_id == self.recommendation.selected_alternative_id:
                    return r
        return None

    def why_not(self, alternative_id: str) -> str | None:
        for wn in self.explanation.why_not:
            if wn.alternative_id == alternative_id:
                return wn.reason
        return None

    def to_canonical_json(self) -> str:
        import json
        return json.dumps(self.model_dump(mode="json"), indent=2, ensure_ascii=False)
