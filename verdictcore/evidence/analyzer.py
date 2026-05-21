"""Evidence quality analyzer — scores reliability, freshness, coverage."""

from __future__ import annotations

from verdictcore.models.decision import DecisionInput
from verdictcore.models.evidence import Evidence
from verdictcore.models.intelligence import (
    EvidenceQualityReport,
    EvidenceQualityScore,
)
from verdictcore.models.result import DecisionResult

SOURCE_TYPE_DEFAULTS: dict[str, float] = {
    "official_document": 0.95,
    "third_party_report": 0.85,
    "api": 0.80,
    "structured_import": 0.80,
    "vendor_statement": 0.65,
    "manual_entry": 0.60,
    "llm_extracted": 0.55,
    "unknown": 0.40,
}


class EvidenceQualityAnalyzer:

    def evaluate(
        self,
        decision_input: DecisionInput,
        decision_result: DecisionResult,
    ) -> EvidenceQualityReport:
        scores: list[EvidenceQualityScore] = []
        warnings: list[str] = []
        winner_id = decision_result.recommendation.selected_alternative_id

        for ev in decision_input.evidence:
            score = self._score_evidence(ev)
            scores.append(score)

            if (
                score.level in ("low", "unknown")
                and ev.alternative_id == winner_id
                and ev.field
            ):
                warnings.append(
                    f"Selected alternative depends on low-quality"
                    f" evidence for {ev.field}."
                )

        if not scores:
            return EvidenceQualityReport(
                decision_id=decision_result.decision_id,
                overall_evidence_quality=0.0,
                level="unknown",
                field_scores=[],
                warnings=["No evidence provided."],
            )

        overall = sum(s.overall_quality for s in scores) / len(scores)
        level = _quality_level(overall)

        return EvidenceQualityReport(
            decision_id=decision_result.decision_id,
            overall_evidence_quality=round(overall, 4),
            level=level,
            field_scores=scores,
            warnings=warnings,
        )

    def _score_evidence(self, ev: Evidence) -> EvidenceQualityScore:
        source_q = SOURCE_TYPE_DEFAULTS.get(ev.source_type, 0.40)
        reliability = ev.reliability if ev.reliability is not None else source_q
        confidence = ev.confidence if ev.confidence is not None else source_q
        freshness = _freshness_score(ev.freshness_days)

        overall = (
            reliability * 0.35
            + confidence * 0.25
            + freshness * 0.20
            + source_q * 0.20
        )
        level = _quality_level(overall)

        notes: list[str] = []
        if ev.reliability is None:
            notes.append(f"Reliability inferred from source type ({ev.source_type}).")
        if ev.freshness_days is None:
            notes.append("Freshness unknown, default score applied.")
        if source_q < 0.65:
            notes.append(f"Source type '{ev.source_type}' has low default quality.")

        return EvidenceQualityScore(
            evidence_id=ev.id,
            alternative_id=ev.alternative_id,
            field=ev.field,
            reliability_score=round(reliability, 4),
            confidence_score=round(confidence, 4),
            freshness_score=round(freshness, 4),
            source_quality=round(source_q, 4),
            overall_quality=round(overall, 4),
            level=level,
            notes=notes,
        )


def _freshness_score(days: int | None) -> float:
    if days is None:
        return 0.5
    if days <= 30:
        return 1.0
    if days <= 90:
        return 0.8
    if days <= 180:
        return 0.6
    if days <= 365:
        return 0.4
    return 0.2


def _quality_level(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.50:
        return "medium"
    if score >= 0.25:
        return "low"
    return "unknown"
