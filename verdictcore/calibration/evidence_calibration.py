"""Evidence source calibration — reliability based on observed accuracy."""

from __future__ import annotations

from pydantic import BaseModel

from verdictcore.models.evidence import Evidence
from verdictcore.models.intelligence import OutcomeRecord


class SourceReliabilityProfile(BaseModel):

    domain: str
    field: str
    source_type: str
    observed_accuracy: float
    sample_size: int
    current_default_reliability: float
    suggested_reliability: float
    confidence: float
    reason: str


class CalibrationReport(BaseModel):

    domain: str
    profiles: list[SourceReliabilityProfile] = []


class EvidenceCalibrator:

    def __init__(
        self,
        default_reliability: float = 0.65,
        acceptable_delta: float = 0.10,
    ) -> None:
        self._default_reliability = default_reliability
        self._acceptable_delta = acceptable_delta

    def calibrate(
        self,
        evidence_list: list[Evidence],
        outcomes: list[OutcomeRecord],
        domain: str = "all",
    ) -> CalibrationReport:
        if not evidence_list or not outcomes:
            return CalibrationReport(domain=domain)

        outcome_map = {o.decision_id: o for o in outcomes}

        source_accuracy: dict[tuple[str, str], list[bool]] = {}

        for ev in evidence_list:
            if not ev.field or not ev.source_type:
                continue

            key = (ev.field, ev.source_type)
            decision_id = getattr(ev, "decision_id", None)
            if decision_id is None:
                continue

            outcome = outcome_map.get(decision_id)
            if outcome is None:
                continue

            actual_key = f"actual_{ev.field}"
            expected_key = f"expected_{ev.field}"
            actual = outcome.outcome_values.get(actual_key)
            expected = outcome.outcome_values.get(expected_key)

            if actual is None or expected is None:
                continue
            if not isinstance(actual, (int, float)):
                continue
            if not isinstance(expected, (int, float)):
                continue
            if float(expected) == 0:
                continue

            delta = abs(float(actual) - float(expected)) / abs(float(expected))
            accurate = delta <= self._acceptable_delta
            source_accuracy.setdefault(key, []).append(accurate)

        profiles: list[SourceReliabilityProfile] = []
        for (field, source_type), results in source_accuracy.items():
            if len(results) < 3:
                continue

            observed = sum(results) / len(results)
            suggested = (
                0.7 * self._default_reliability + 0.3 * observed
            )
            confidence = min(1.0, len(results) / 100)

            reason = (
                f"{source_type} evidence for {field} was accurate"
                f" in {observed:.0%} of {len(results)} outcomes."
            )
            if observed < 0.5:
                reason += " Consider requiring stronger evidence sources."

            profiles.append(SourceReliabilityProfile(
                domain=domain,
                field=field,
                source_type=source_type,
                observed_accuracy=round(observed, 3),
                sample_size=len(results),
                current_default_reliability=self._default_reliability,
                suggested_reliability=round(suggested, 3),
                confidence=round(confidence, 3),
                reason=reason,
            ))

        return CalibrationReport(domain=domain, profiles=profiles)
