"""Outcome tracker — record actuals and compute decision quality."""

from __future__ import annotations

from verdictcore.models.intelligence import (
    DecisionQualityReport,
    OutcomeRecord,
)
from verdictcore.models.result import DecisionResult


class OutcomeTracker:

    def record_and_evaluate(
        self,
        decision_result: DecisionResult,
        outcome: OutcomeRecord,
    ) -> DecisionQualityReport:
        expected_score = self._compute_expected_score(decision_result)
        actual_score = self._compute_actual_score(
            decision_result, outcome,
        )

        delta = None
        if expected_score is not None and actual_score is not None:
            delta = round(actual_score - expected_score, 4)

        gaps = self._find_gaps(decision_result, outcome)
        lessons = self._derive_lessons(gaps)
        quality = _quality_level(delta)

        return DecisionQualityReport(
            decision_id=decision_result.decision_id,
            selected_alternative_id=outcome.selected_alternative_id,
            expected_score=expected_score,
            actual_score=actual_score,
            delta=delta,
            quality_level=quality,
            main_gaps=gaps,
            lessons=lessons,
        )

    @staticmethod
    def _compute_expected_score(result: DecisionResult) -> float | None:
        selected = result.selected
        if selected is None:
            return None
        return round(selected.total_score, 4)

    @staticmethod
    def _compute_actual_score(
        result: DecisionResult,
        outcome: OutcomeRecord,
    ) -> float | None:
        selected = result.selected
        if selected is None or selected.calculation_trace is None:
            return None

        trace = selected.calculation_trace
        total = 0.0
        count = 0

        for crit_name, crit_trace in trace.criteria.items():
            expected_key = f"expected_{crit_name}"
            actual_key = f"actual_{crit_name}"

            actual_val = outcome.outcome_values.get(actual_key)
            expected_val = outcome.outcome_values.get(expected_key)

            if actual_val is None or not isinstance(actual_val, (int, float)):
                actual_val = outcome.outcome_values.get(crit_name)
            if actual_val is None or not isinstance(actual_val, (int, float)):
                continue

            if expected_val is None or not isinstance(expected_val, (int, float)):
                if crit_trace.raw is not None:
                    expected_val = float(crit_trace.raw)
                else:
                    continue

            if float(expected_val) == 0:
                continue

            ratio = float(actual_val) / float(expected_val)
            capped = min(ratio, 1.5)
            total += capped * crit_trace.weight
            count += 1

        if count == 0:
            return None
        return round(total / count * 100, 4)

    @staticmethod
    def _find_gaps(
        result: DecisionResult,
        outcome: OutcomeRecord,
    ) -> list[str]:
        gaps: list[str] = []
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

            expected_f = float(expected_val)
            actual_f = float(actual_val)
            if expected_f == 0:
                continue

            pct = abs(actual_f - expected_f) / expected_f * 100
            if pct > 10:
                direction = "exceeded" if actual_f > expected_f else "fell short of"
                gaps.append(
                    f"{field}: actual ({actual_f}) {direction}"
                    f" expected ({expected_f}) by {pct:.0f}%."
                )

        return gaps

    @staticmethod
    def _derive_lessons(gaps: list[str]) -> list[str]:
        lessons: list[str] = []
        for gap in gaps:
            field = gap.split(":")[0].strip()
            if "exceeded" in gap:
                lessons.append(
                    f"Consider adjusting expected {field} estimates"
                    f" or reviewing evidence accuracy."
                )
            elif "fell short" in gap:
                lessons.append(
                    f"{field} underperformed. Increase weight or"
                    f" require stronger evidence in future decisions."
                )
        return lessons


def _quality_level(delta: float | None) -> str:
    if delta is None:
        return "unknown"
    if delta >= -5.0:
        return "high"
    if delta >= -15.0:
        return "medium"
    return "low"
