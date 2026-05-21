"""Tests for Outcome Learning Lite."""

from verdictcore import Alternative, Criterion, DecisionInput, Deciwa
from verdictcore.learning import OutcomeLearningAnalyzer
from verdictcore.models.intelligence import OutcomeRecord


def _make_result(decision_id: str):
    decision = DecisionInput(
        decision_id=decision_id,
        question="Which?",
        domain="test",
        criteria=[
            Criterion(name="cost", weight=0.5, direction="minimize"),
            Criterion(name="quality", weight=0.5, direction="maximize"),
        ],
        alternatives=[
            Alternative(id="a", name="A", values={"cost": 100, "quality": 90}),
            Alternative(id="b", name="B", values={"cost": 80, "quality": 75}),
        ],
    )
    return Deciwa(enable_sensitivity=False).run(decision)


class TestOutcomeLearning:

    def test_empty_data_returns_empty(self):
        analyzer = OutcomeLearningAnalyzer()
        report = analyzer.analyze([], [], policy_id="test_policy")
        assert report.decisions_analyzed == 0
        assert report.patterns == []

    def test_detects_overestimation(self):
        results = [_make_result(f"d_{i}") for i in range(5)]
        outcomes = [
            OutcomeRecord(
                decision_id=f"d_{i}",
                selected_alternative_id="a",
                outcome_values={
                    "actual_cost": 150,
                    "expected_cost": 100,
                    "actual_quality": 70,
                    "expected_quality": 90,
                },
            )
            for i in range(5)
        ]

        analyzer = OutcomeLearningAnalyzer()
        report = analyzer.analyze(results, outcomes, policy_id="test")

        assert report.decisions_analyzed == 5
        assert len(report.patterns) >= 1
        types = [p.pattern_type for p in report.patterns]
        assert "criterion_overestimation" in types

    def test_no_pattern_if_outcomes_match(self):
        results = [_make_result(f"d_{i}") for i in range(5)]
        outcomes = [
            OutcomeRecord(
                decision_id=f"d_{i}",
                selected_alternative_id="a",
                outcome_values={
                    "actual_cost": 101,
                    "expected_cost": 100,
                    "actual_quality": 89,
                    "expected_quality": 90,
                },
            )
            for i in range(5)
        ]

        analyzer = OutcomeLearningAnalyzer()
        report = analyzer.analyze(results, outcomes)
        assert report.patterns == []

    def test_detects_underperformance(self):
        results = [_make_result(f"d_{i}") for i in range(5)]
        outcomes = [
            OutcomeRecord(
                decision_id=f"d_{i}",
                selected_alternative_id="a",
                outcome_values={
                    "actual_quality": 60,
                    "expected_quality": 90,
                },
            )
            for i in range(5)
        ]

        analyzer = OutcomeLearningAnalyzer()
        report = analyzer.analyze(results, outcomes)
        types = [p.pattern_type for p in report.patterns]
        assert "criterion_underperformance" in types
