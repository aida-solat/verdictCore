"""Outcome learning analyzer — detect patterns from historical outcomes."""

from __future__ import annotations

from pydantic import BaseModel

from verdictcore.models.intelligence import OutcomeRecord
from verdictcore.models.result import DecisionResult


class LearningPattern(BaseModel):

    pattern_type: str
    target: str
    finding: str
    recommendation: str
    confidence: float = 0.0


class LearningReport(BaseModel):

    policy_id: str | None = None
    decisions_analyzed: int = 0
    patterns: list[LearningPattern] = []


class OutcomeLearningAnalyzer:

    def analyze(
        self,
        results: list[DecisionResult],
        outcomes: list[OutcomeRecord],
        policy_id: str | None = None,
    ) -> LearningReport:
        if not results or not outcomes:
            return LearningReport(
                policy_id=policy_id,
                decisions_analyzed=0,
            )

        outcome_map = self._build_outcome_map(outcomes)
        patterns: list[LearningPattern] = []

        overestimation = self._detect_overestimation(results, outcome_map)
        patterns.extend(overestimation)

        return LearningReport(
            policy_id=policy_id,
            decisions_analyzed=len(results),
            patterns=patterns,
        )

    def _detect_overestimation(
        self,
        results: list[DecisionResult],
        outcome_map: dict[str, list[OutcomeRecord]],
    ) -> list[LearningPattern]:
        patterns: list[LearningPattern] = []
        field_deltas: dict[str, list[float]] = {}

        for result in results:
            decision_outcomes = outcome_map.get(result.decision_id, [])
            for outcome in decision_outcomes:
                for key, actual_val in outcome.outcome_values.items():
                    if not key.startswith("actual_"):
                        continue
                    field = key.removeprefix("actual_")
                    expected_key = f"expected_{field}"
                    expected_val = outcome.outcome_values.get(expected_key)

                    if expected_val is None or actual_val is None:
                        continue
                    if not isinstance(expected_val, (int, float)):
                        continue
                    if not isinstance(actual_val, (int, float)):
                        continue
                    if float(expected_val) == 0:
                        continue

                    delta_pct = (
                        (float(actual_val) - float(expected_val))
                        / float(expected_val) * 100
                    )
                    field_deltas.setdefault(field, []).append(delta_pct)

        for field, deltas in field_deltas.items():
            if len(deltas) < 2:
                continue
            avg_delta = sum(deltas) / len(deltas)
            overestimated_count = sum(1 for d in deltas if d > 10)
            overestimation_rate = overestimated_count / len(deltas)

            if overestimation_rate >= 0.5:
                patterns.append(LearningPattern(
                    pattern_type="criterion_overestimation",
                    target=field,
                    finding=(
                        f"{field} estimates were optimistic in"
                        f" {overestimation_rate:.0%} of outcomes."
                    ),
                    recommendation=(
                        f"Increase evidence requirements for {field}"
                        f" or penalize estimated values."
                    ),
                    confidence=min(overestimation_rate, 0.95),
                ))
            elif avg_delta < -15:
                patterns.append(LearningPattern(
                    pattern_type="criterion_underperformance",
                    target=field,
                    finding=(
                        f"{field} consistently underperformed"
                        f" expectations (avg delta: {avg_delta:.1f}%)."
                    ),
                    recommendation=(
                        f"Increase weight of {field} or require"
                        f" stronger evidence."
                    ),
                    confidence=min(abs(avg_delta) / 100, 0.90),
                ))

        return patterns

    @staticmethod
    def _build_outcome_map(
        outcomes: list[OutcomeRecord],
    ) -> dict[str, list[OutcomeRecord]]:
        mapping: dict[str, list[OutcomeRecord]] = {}
        for o in outcomes:
            mapping.setdefault(o.decision_id, []).append(o)
        return mapping
