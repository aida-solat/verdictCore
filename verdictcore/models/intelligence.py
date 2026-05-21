"""v2 intelligence models — VoI, evidence quality, robustness, outcomes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class MissingInformationItem(BaseModel):

    alternative_id: str
    field: str
    criterion_weight: float
    constraint_related: bool = False
    near_threshold: bool = False
    estimated_impact: float = Field(ge=0.0, le=1.0)
    reason: str
    suggested_question: str


class ValueOfInformationReport(BaseModel):

    decision_id: str
    items: list[MissingInformationItem] = []

    @property
    def top_items(self) -> list[MissingInformationItem]:
        return sorted(self.items, key=lambda x: x.estimated_impact, reverse=True)


class EvidenceQualityScore(BaseModel):

    evidence_id: str
    alternative_id: str | None = None
    field: str | None = None
    reliability_score: float | None = None
    confidence_score: float | None = None
    freshness_score: float | None = None
    source_quality: float | None = None
    overall_quality: float = Field(ge=0.0, le=1.0)
    level: Literal["high", "medium", "low", "unknown"]
    notes: list[str] = []


class EvidenceQualityReport(BaseModel):

    decision_id: str
    overall_evidence_quality: float = Field(ge=0.0, le=1.0)
    level: Literal["high", "medium", "low", "unknown"]
    field_scores: list[EvidenceQualityScore] = []
    warnings: list[str] = []


class RobustnessReport(BaseModel):

    decision_id: str
    selected_alternative_id: str | None = None
    stability_score: float = Field(ge=0.0, le=1.0)
    scenario_consistency_score: float = Field(ge=0.0, le=1.0)
    data_completeness_score: float = Field(ge=0.0, le=1.0)
    evidence_quality_score: float = Field(ge=0.0, le=1.0)
    constraint_risk_score: float = Field(ge=0.0, le=1.0)
    overall_robustness_score: float = Field(ge=0.0, le=1.0)
    level: Literal["strong", "moderate", "fragile", "weak"]
    key_risks: list[str] = []
    recommendations: list[str] = []


class OutcomeRecord(BaseModel):

    decision_id: str
    selected_alternative_id: str
    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    outcome_values: dict[str, float | int | str | bool | None]
    notes: str | None = None
    metadata: dict[str, Any] = {}


class DecisionQualityReport(BaseModel):

    decision_id: str
    selected_alternative_id: str | None = None
    expected_score: float | None = None
    actual_score: float | None = None
    delta: float | None = None
    quality_level: Literal["high", "medium", "low", "unknown"]
    main_gaps: list[str] = []
    lessons: list[str] = []


class IntelligenceReport(BaseModel):
    """Unified v2 intelligence output."""

    decision_id: str
    scenario_analysis: dict[str, Any] = {}
    value_of_information: ValueOfInformationReport | None = None
    evidence_quality: EvidenceQualityReport | None = None
    robustness: RobustnessReport | None = None
