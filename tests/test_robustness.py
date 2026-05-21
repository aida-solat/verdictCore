"""Tests for Robustness analyzer."""

import pytest

from verdictcore import (
    Alternative,
    Constraint,
    Criterion,
    DecisionInput,
    Deciwa,
    Evidence,
)
from verdictcore.evidence import EvidenceQualityAnalyzer
from verdictcore.models.scenario import Scenario
from verdictcore.robustness import RobustnessAnalyzer
from verdictcore.scenarios import ScenarioEngine


@pytest.fixture
def supplier_decision() -> DecisionInput:
    return DecisionInput(
        decision_id="test_robust_001",
        question="Which supplier?",
        domain="supplier_selection",
        criteria=[
            Criterion(name="cost", weight=0.25, direction="minimize"),
            Criterion(name="compliance", weight=0.35, direction="maximize"),
            Criterion(name="security", weight=0.25, direction="maximize"),
            Criterion(name="delivery", weight=0.15, direction="minimize"),
        ],
        constraints=[
            Constraint(
                field="compliance", operator=">=", value=85, action="block",
            ),
        ],
        alternatives=[
            Alternative(
                id="a", name="Supplier A",
                values={
                    "cost": 480000, "compliance": 82,
                    "security": 88, "delivery": 30,
                },
            ),
            Alternative(
                id="b", name="Supplier B",
                values={
                    "cost": 510000, "compliance": 91,
                    "security": 90, "delivery": 21,
                },
            ),
            Alternative(
                id="c", name="Supplier C",
                values={
                    "cost": 450000, "compliance": 95,
                    "security": 86, "delivery": 18,
                },
            ),
        ],
        evidence=[
            Evidence(
                id="ev1", alternative_id="b", field="compliance",
                source="cert.pdf", source_type="official_document",
                claim="ISO cert", value=91,
                confidence=0.92, reliability=0.95, freshness_days=60,
            ),
        ],
    )


class TestRobustness:

    def test_basic_robustness(self, supplier_decision):
        engine = Deciwa(enable_sensitivity=True)
        result = engine.run(supplier_decision)
        analyzer = RobustnessAnalyzer()
        report = analyzer.analyze(supplier_decision, result)

        assert 0.0 <= report.overall_robustness_score <= 1.0
        assert report.level in ("strong", "moderate", "fragile", "weak")
        assert report.decision_id == "test_robust_001"

    def test_with_scenarios(self, supplier_decision):
        deciwa = Deciwa(enable_sensitivity=True)
        result = deciwa.run(supplier_decision)
        se = ScenarioEngine(deciwa)
        scenarios = [
            Scenario(
                id="s1", name="Cost Heavy",
                criteria_overrides={
                    "cost": 0.60, "compliance": 0.15,
                    "security": 0.15, "delivery": 0.10,
                },
            ),
        ]
        scenario_results = se.run(supplier_decision, scenarios)

        analyzer = RobustnessAnalyzer()
        report = analyzer.analyze(
            supplier_decision, result,
            scenario_results=scenario_results,
        )
        assert 0.0 <= report.scenario_consistency_score <= 1.0

    def test_with_evidence_quality(self, supplier_decision):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(supplier_decision)

        eq = EvidenceQualityAnalyzer()
        eq_report = eq.evaluate(supplier_decision, result)

        analyzer = RobustnessAnalyzer()
        report = analyzer.analyze(
            supplier_decision, result,
            evidence_quality_report=eq_report,
        )
        assert report.evidence_quality_score > 0.0

    def test_data_completeness(self, supplier_decision):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(supplier_decision)
        analyzer = RobustnessAnalyzer()
        report = analyzer.analyze(supplier_decision, result)
        assert report.data_completeness_score == 1.0

    def test_incomplete_data_lowers_completeness(self):
        decision = DecisionInput(
            decision_id="test_robust_002",
            question="Missing data?",
            domain="test",
            criteria=[
                Criterion(name="a", weight=0.5, direction="maximize"),
                Criterion(name="b", weight=0.5, direction="maximize"),
            ],
            alternatives=[
                Alternative(id="x", name="X", values={"a": 90, "b": None}),
                Alternative(id="y", name="Y", values={"a": 80, "b": 70}),
            ],
        )
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision)
        analyzer = RobustnessAnalyzer()
        report = analyzer.analyze(decision, result)
        assert report.data_completeness_score < 1.0

    def test_risks_and_recommendations(self):
        decision = DecisionInput(
            decision_id="test_robust_003",
            question="Risky?",
            domain="test",
            criteria=[
                Criterion(name="score", weight=0.5, direction="maximize"),
                Criterion(name="other", weight=0.5, direction="maximize"),
            ],
            alternatives=[
                Alternative(
                    id="x", name="X",
                    values={"score": 90, "other": None},
                ),
                Alternative(
                    id="y", name="Y",
                    values={"score": 80, "other": 70},
                ),
            ],
        )
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision)
        analyzer = RobustnessAnalyzer()
        report = analyzer.analyze(decision, result)
        assert isinstance(report.key_risks, list)
        assert isinstance(report.recommendations, list)
