"""Drift detection — detect changes in decision patterns over time."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from verdictcore.models.intelligence import OutcomeRecord
from verdictcore.models.result import DecisionResult


class DriftSignal(BaseModel):

    id: str
    policy_id: str | None = None
    drift_type: Literal[
        "outcome_drift",
        "criterion_drift",
        "evidence_drift",
        "constraint_drift",
        "override_drift",
    ]
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    confidence: float = 0.0
    recommended_action: str = ""


class DriftReport(BaseModel):

    policy_id: str | None = None
    signals: list[DriftSignal] = []
    overall_drift_level: Literal["none", "low", "medium", "high"] = "none"


class DriftDetector:

    def detect(
        self,
        results: list[DecisionResult],
        outcomes: list[OutcomeRecord] | None = None,
        policy_id: str | None = None,
    ) -> DriftReport:
        if not results:
            return DriftReport(policy_id=policy_id)

        signals: list[DriftSignal] = []

        signals.extend(self._detect_outcome_drift(results, outcomes))
        signals.extend(self._detect_constraint_drift(results))

        level = self._assess_level(signals)

        return DriftReport(
            policy_id=policy_id,
            signals=signals,
            overall_drift_level=level,
        )

    def _detect_outcome_drift(
        self,
        results: list[DecisionResult],
        outcomes: list[OutcomeRecord] | None,
    ) -> list[DriftSignal]:
        signals: list[DriftSignal] = []
        if not outcomes or len(outcomes) < 5:
            return signals

        outcome_map = {o.decision_id: o for o in outcomes}

        half = len(results) // 2
        recent = results[:half]
        older = results[half:]

        recent_poor = sum(
            1 for r in recent
            if outcome_map.get(r.decision_id)
            and self._is_poor_outcome(outcome_map[r.decision_id])
        )
        older_poor = sum(
            1 for r in older
            if outcome_map.get(r.decision_id)
            and self._is_poor_outcome(outcome_map[r.decision_id])
        )

        recent_total = max(len(recent), 1)
        older_total = max(len(older), 1)

        recent_rate = recent_poor / recent_total
        older_rate = older_poor / older_total

        if recent_rate > older_rate + 0.15:
            severity = "high" if recent_rate > older_rate + 0.30 else "medium"
            signals.append(DriftSignal(
                id="drift_outcome_001",
                drift_type="outcome_drift",
                severity=severity,
                description=(
                    f"Poor outcome rate increased from {older_rate:.0%}"
                    f" to {recent_rate:.0%} in recent decisions."
                ),
                confidence=min(0.95, 0.5 + (recent_rate - older_rate)),
                recommended_action=(
                    "Review policy effectiveness and evidence requirements."
                ),
            ))

        return signals

    def _detect_constraint_drift(
        self, results: list[DecisionResult],
    ) -> list[DriftSignal]:
        signals: list[DriftSignal] = []
        if len(results) < 10:
            return signals

        half = len(results) // 2
        recent = results[:half]
        older = results[half:]

        recent_blocked = sum(
            1 for r in recent if r.status.value == "blocked"
        )
        older_blocked = sum(
            1 for r in older if r.status.value == "blocked"
        )

        recent_rate = recent_blocked / max(len(recent), 1)
        older_rate = older_blocked / max(len(older), 1)

        if recent_rate > older_rate + 0.15:
            signals.append(DriftSignal(
                id="drift_constraint_001",
                drift_type="constraint_drift",
                severity="medium",
                description=(
                    f"Blocked rate increased from {older_rate:.0%}"
                    f" to {recent_rate:.0%}."
                ),
                confidence=min(0.90, 0.4 + (recent_rate - older_rate)),
                recommended_action=(
                    "Check if constraints are still appropriate for"
                    " current market conditions."
                ),
            ))

        return signals

    @staticmethod
    def _is_poor_outcome(outcome: OutcomeRecord) -> bool:
        for key, val in outcome.outcome_values.items():
            if key.startswith("actual_") and isinstance(val, (int, float)):
                expected_key = f"expected_{key.removeprefix('actual_')}"
                expected = outcome.outcome_values.get(expected_key)
                if expected and isinstance(expected, (int, float)):
                    if float(expected) == 0:
                        continue
                    delta = (
                        abs(float(val) - float(expected)) / abs(float(expected))
                    )
                    if delta > 0.25:
                        return True
        return False

    @staticmethod
    def _assess_level(
        signals: list[DriftSignal],
    ) -> Literal["none", "low", "medium", "high"]:
        if not signals:
            return "none"
        severities = [s.severity for s in signals]
        if "critical" in severities or "high" in severities:
            return "high"
        if "medium" in severities:
            return "medium"
        return "low"
