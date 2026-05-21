"""Tests for Stress Testing Engine."""

import pytest

from verdictcore import Alternative, Criterion, DecisionInput
from verdictcore.models.constraint import Constraint
from verdictcore.stress import Perturbation, StressScenario, StressTestEngine


@pytest.fixture
def supplier_decision() -> DecisionInput:
    return DecisionInput(
        decision_id="stress_test_001",
        question="Which supplier under stress?",
        domain="supplier_selection",
        criteria=[
            Criterion(name="cost", weight=0.35, direction="minimize"),
            Criterion(name="compliance", weight=0.35, direction="maximize"),
            Criterion(name="security", weight=0.30, direction="maximize"),
        ],
        constraints=[
            Constraint(field="security", operator=">=", value=75, action="block"),
        ],
        alternatives=[
            Alternative(
                id="a", name="A",
                values={"cost": 500000, "compliance": 88, "security": 85},
            ),
            Alternative(
                id="b", name="B",
                values={"cost": 480000, "compliance": 91, "security": 90},
            ),
            Alternative(
                id="c", name="C",
                values={"cost": 450000, "compliance": 80, "security": 78},
            ),
        ],
    )


class TestStressTestEngine:

    def test_basic_stress(self, supplier_decision):
        scenarios = [
            StressScenario(
                id="cost_up_20",
                name="Cost +20%",
                perturbations=[
                    Perturbation(
                        target="all_values", field="cost",
                        operation="multiply", value=1.20,
                    ),
                ],
            ),
        ]
        engine = StressTestEngine()
        report = engine.run(supplier_decision, scenarios)

        assert report.decision_id == "stress_test_001"
        assert report.base_winner is not None
        assert len(report.stress_results) == 1

    def test_winner_change_detected(self, supplier_decision):
        scenarios = [
            StressScenario(
                id="cost_dominant",
                name="Cost weight to 0.80",
                perturbations=[
                    Perturbation(
                        target="criterion", field="cost",
                        operation="set", value=0.80,
                    ),
                    Perturbation(
                        target="criterion", field="compliance",
                        operation="set", value=0.10,
                    ),
                    Perturbation(
                        target="criterion", field="security",
                        operation="set", value=0.10,
                    ),
                ],
            ),
        ]
        engine = StressTestEngine()
        report = engine.run(supplier_decision, scenarios)

        cost_stress = report.stress_results[0]
        assert cost_stress.winner == "c"
        assert cost_stress.winner_changed is True
        assert cost_stress.risk_level == "high"

    def test_resilient_scenario(self, supplier_decision):
        scenarios = [
            StressScenario(
                id="minor_cost",
                name="Cost +5%",
                perturbations=[
                    Perturbation(
                        target="all_values", field="cost",
                        operation="multiply", value=1.05,
                    ),
                ],
            ),
        ]
        engine = StressTestEngine()
        report = engine.run(supplier_decision, scenarios)

        assert report.stress_results[0].winner_changed is False
        assert report.stress_results[0].risk_level == "low"

    def test_constraint_stress(self, supplier_decision):
        scenarios = [
            StressScenario(
                id="strict_security",
                name="Security >= 88",
                perturbations=[
                    Perturbation(
                        target="constraint", field="security",
                        operation="set", value=88,
                    ),
                ],
            ),
        ]
        engine = StressTestEngine()
        report = engine.run(supplier_decision, scenarios)
        assert len(report.stress_results) == 1

    def test_vulnerability_assessment(self, supplier_decision):
        scenarios = [
            StressScenario(
                id="s1", name="S1",
                perturbations=[
                    Perturbation(
                        target="criterion", field="cost",
                        operation="set", value=0.80,
                    ),
                    Perturbation(
                        target="criterion", field="compliance",
                        operation="set", value=0.10,
                    ),
                    Perturbation(
                        target="criterion", field="security",
                        operation="set", value=0.10,
                    ),
                ],
            ),
            StressScenario(
                id="s2", name="S2",
                perturbations=[
                    Perturbation(
                        target="criterion", field="compliance",
                        operation="set", value=0.80,
                    ),
                    Perturbation(
                        target="criterion", field="cost",
                        operation="set", value=0.10,
                    ),
                    Perturbation(
                        target="criterion", field="security",
                        operation="set", value=0.10,
                    ),
                ],
            ),
        ]
        engine = StressTestEngine()
        report = engine.run(supplier_decision, scenarios)
        assert report.overall_vulnerability in ("low", "medium", "high")

    def test_interpretation(self, supplier_decision):
        scenarios = [
            StressScenario(
                id="s1", name="Test Stress",
                perturbations=[
                    Perturbation(
                        target="all_values", field="cost",
                        operation="multiply", value=1.05,
                    ),
                ],
            ),
        ]
        engine = StressTestEngine()
        report = engine.run(supplier_decision, scenarios)
        assert report.stress_results[0].interpretation != ""
