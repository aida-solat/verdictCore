"""Tests for Policy Drift Detection."""

from verdictcore import Alternative, Criterion, DecisionInput, Deciwa
from verdictcore.drift import DriftDetector
from verdictcore.models.intelligence import OutcomeRecord


def _make_results(count: int = 20):
    results = []
    for i in range(count):
        decision = DecisionInput(
            decision_id=f"drift_{i}",
            question="Test?",
            domain="test",
            criteria=[
                Criterion(name="score", weight=1.0, direction="maximize"),
            ],
            alternatives=[
                Alternative(id="a", name="A", values={"score": 90}),
                Alternative(id="b", name="B", values={"score": 80}),
            ],
        )
        results.append(Deciwa(enable_sensitivity=False).run(decision))
    return results


class TestDriftDetector:

    def test_no_drift_stable_outcomes(self):
        results = _make_results(20)
        outcomes = [
            OutcomeRecord(
                decision_id=f"drift_{i}",
                selected_alternative_id="a",
                outcome_values={
                    "actual_score": 89, "expected_score": 90,
                },
            )
            for i in range(20)
        ]
        detector = DriftDetector()
        report = detector.detect(results, outcomes)
        assert report.overall_drift_level == "none"

    def test_outcome_drift_detected(self):
        results = _make_results(20)
        outcomes = []
        for i in range(20):
            if i < 10:
                # Recent half (first 10) have poor outcomes
                outcomes.append(OutcomeRecord(
                    decision_id=f"drift_{i}",
                    selected_alternative_id="a",
                    outcome_values={
                        "actual_score": 50, "expected_score": 90,
                    },
                ))
            else:
                # Older half (last 10) have good outcomes
                outcomes.append(OutcomeRecord(
                    decision_id=f"drift_{i}",
                    selected_alternative_id="a",
                    outcome_values={
                        "actual_score": 88, "expected_score": 90,
                    },
                ))

        detector = DriftDetector()
        report = detector.detect(results, outcomes)
        assert report.overall_drift_level in ("medium", "high")
        assert len(report.signals) >= 1

    def test_empty_results(self):
        detector = DriftDetector()
        report = detector.detect([])
        assert report.overall_drift_level == "none"

    def test_insufficient_outcomes_no_drift(self):
        results = _make_results(5)
        detector = DriftDetector()
        report = detector.detect(results, [])
        assert report.overall_drift_level == "none"
