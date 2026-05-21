"""Tests for Outcome Tracker."""

import pytest

from verdictcore import Alternative, Criterion, DecisionInput, Deciwa
from verdictcore.models.intelligence import OutcomeRecord
from verdictcore.outcomes import OutcomeTracker


@pytest.fixture
def simple_decision() -> DecisionInput:
    return DecisionInput(
        decision_id="test_outcome_001",
        question="Which option?",
        domain="test",
        criteria=[
            Criterion(name="cost", weight=0.4, direction="minimize"),
            Criterion(name="quality", weight=0.6, direction="maximize"),
        ],
        alternatives=[
            Alternative(
                id="a", name="Option A",
                values={"cost": 100, "quality": 90},
            ),
            Alternative(
                id="b", name="Option B",
                values={"cost": 80, "quality": 75},
            ),
        ],
    )


class TestOutcomeTracker:

    def test_basic_outcome_tracking(self, simple_decision):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(simple_decision)
        winner_id = result.recommendation.selected_alternative_id

        tracker = OutcomeTracker()
        outcome = OutcomeRecord(
            decision_id="test_outcome_001",
            selected_alternative_id=winner_id or "a",
            outcome_values={
                "actual_cost": 110,
                "expected_cost": 100,
                "actual_quality": 85,
                "expected_quality": 90,
            },
        )
        report = tracker.record_and_evaluate(result, outcome)

        assert report.decision_id == "test_outcome_001"
        assert report.quality_level in ("high", "medium", "low", "unknown")

    def test_gap_detection(self, simple_decision):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(simple_decision)
        winner_id = result.recommendation.selected_alternative_id

        tracker = OutcomeTracker()
        outcome = OutcomeRecord(
            decision_id="test_outcome_001",
            selected_alternative_id=winner_id or "a",
            outcome_values={
                "actual_cost": 150,
                "expected_cost": 100,
                "actual_quality": 70,
                "expected_quality": 90,
            },
        )
        report = tracker.record_and_evaluate(result, outcome)
        assert len(report.main_gaps) >= 1

    def test_lessons_derived(self, simple_decision):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(simple_decision)
        winner_id = result.recommendation.selected_alternative_id

        tracker = OutcomeTracker()
        outcome = OutcomeRecord(
            decision_id="test_outcome_001",
            selected_alternative_id=winner_id or "a",
            outcome_values={
                "actual_cost": 150,
                "expected_cost": 100,
                "actual_quality": 70,
                "expected_quality": 90,
            },
        )
        report = tracker.record_and_evaluate(result, outcome)
        assert len(report.lessons) >= 1

    def test_high_quality_outcome(self, simple_decision):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(simple_decision)
        winner_id = result.recommendation.selected_alternative_id

        tracker = OutcomeTracker()
        outcome = OutcomeRecord(
            decision_id="test_outcome_001",
            selected_alternative_id=winner_id or "a",
            outcome_values={
                "actual_cost": 102,
                "expected_cost": 100,
                "actual_quality": 89,
                "expected_quality": 90,
            },
        )
        report = tracker.record_and_evaluate(result, outcome)
        assert report.main_gaps == []

    def test_no_outcome_values_returns_unknown(self, simple_decision):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(simple_decision)

        tracker = OutcomeTracker()
        outcome = OutcomeRecord(
            decision_id="test_outcome_001",
            selected_alternative_id="a",
            outcome_values={},
        )
        report = tracker.record_and_evaluate(result, outcome)
        assert report.quality_level == "unknown"
