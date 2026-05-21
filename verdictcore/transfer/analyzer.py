"""Cross-domain transfer — identify reusable patterns between domains."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from verdictcore.patterns.discovery import DecisionPattern


class TransferCandidate(BaseModel):

    source_domain: str
    target_domain: str
    pattern_id: str
    similarity_score: float
    transfer_confidence: float
    suggested_adaptation: str
    risk: Literal["low", "medium", "high"]


class TransferReport(BaseModel):

    source_domain: str
    target_domain: str
    candidates: list[TransferCandidate] = []


class TransferAnalyzer:

    def analyze(
        self,
        source_patterns: list[DecisionPattern],
        target_domain: str,
        target_criteria: list[str] | None = None,
    ) -> TransferReport:
        if not source_patterns:
            return TransferReport(
                source_domain="none",
                target_domain=target_domain,
            )

        source_domain = source_patterns[0].domain
        candidates: list[TransferCandidate] = []

        for pattern in source_patterns:
            similarity = self._compute_similarity(
                pattern, target_domain, target_criteria,
            )
            if similarity >= 0.4:
                adaptation = self._suggest_adaptation(pattern)
                candidates.append(TransferCandidate(
                    source_domain=pattern.domain,
                    target_domain=target_domain,
                    pattern_id=pattern.id,
                    similarity_score=round(similarity, 3),
                    transfer_confidence=round(
                        similarity * pattern.confidence, 3,
                    ),
                    suggested_adaptation=adaptation,
                    risk=self._assess_risk(similarity),
                ))

        candidates.sort(key=lambda c: c.transfer_confidence, reverse=True)

        return TransferReport(
            source_domain=source_domain,
            target_domain=target_domain,
            candidates=candidates,
        )

    @staticmethod
    def _compute_similarity(
        pattern: DecisionPattern,
        target_domain: str,
        target_criteria: list[str] | None,
    ) -> float:
        score = 0.5

        if pattern.pattern_type == "fragility_pattern":
            score += 0.2

        if pattern.pattern_type == "constraint_failure_pattern":
            score += 0.1

        if pattern.confidence >= 0.7:
            score += 0.1

        if pattern.support_count >= 20:
            score += 0.1

        return min(score, 1.0)

    @staticmethod
    def _suggest_adaptation(pattern: DecisionPattern) -> str:
        if pattern.recommendation_hint:
            return pattern.recommendation_hint
        return (
            f"Apply pattern '{pattern.pattern_type}' with"
            f" domain-specific thresholds."
        )

    @staticmethod
    def _assess_risk(similarity: float) -> Literal["low", "medium", "high"]:
        if similarity >= 0.7:
            return "low"
        if similarity >= 0.5:
            return "medium"
        return "high"
