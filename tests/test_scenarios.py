"""Tests for the Scenario Engine."""

import pytest

from verdictcore import Alternative, Constraint, Criterion, DecisionInput, Deciwa
from verdictcore.models.scenario import Scenario
from verdictcore.scenarios import ScenarioEngine


@pytest.fixture
def supplier_decision() -> DecisionInput:
    return DecisionInput(
        decision_id="test_scenario_001",
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
    )


class TestScenarioEngine:

    def test_basic_scenario_run(self, supplier_decision):
        engine = ScenarioEngine()
        scenarios = [
            Scenario(
                id="cost_sensitive", name="Cost Sensitive",
                criteria_overrides={
                    "cost": 0.60, "compliance": 0.15,
                    "security": 0.15, "delivery": 0.10,
                },
            ),
        ]
        results = engine.run(supplier_decision, scenarios)
        assert len(results) == 1
        assert results[0].scenario_id == "cost_sensitive"
        assert results[0].status.value in (
            "decided", "blocked", "needs_review",
        )

    def test_winner_changes_under_scenario(self, supplier_decision):
        engine = ScenarioEngine()
        Deciwa(enable_sensitivity=False).run(supplier_decision)

        scenarios = [
            Scenario(
                id="cost_dominant", name="Cost Dominant",
                criteria_overrides={
                    "cost": 0.70, "compliance": 0.10,
                    "security": 0.10, "delivery": 0.10,
                },
            ),
        ]
        results = engine.run(supplier_decision, scenarios)
        assert isinstance(results[0].changed_from_base, bool)
        assert results[0].explanation

    def test_consistency_score(self, supplier_decision):
        engine = ScenarioEngine()
        base_result = Deciwa(enable_sensitivity=False).run(supplier_decision)

        scenarios = [
            Scenario(
                id="s1", name="S1",
                criteria_overrides={
                    "cost": 0.25, "compliance": 0.35,
                    "security": 0.25, "delivery": 0.15,
                },
            ),
            Scenario(
                id="s2", name="S2",
                criteria_overrides={
                    "cost": 0.70, "compliance": 0.10,
                    "security": 0.10, "delivery": 0.10,
                },
            ),
        ]
        results = engine.run(supplier_decision, scenarios)
        score = engine.consistency_score(base_result, results)
        assert 0.0 <= score <= 1.0

    def test_empty_scenarios(self, supplier_decision):
        engine = ScenarioEngine()
        results = engine.run(supplier_decision, [])
        assert results == []

    def test_policy_delta_computed(self, supplier_decision):
        engine = ScenarioEngine()
        scenarios = [
            Scenario(
                id="s1", name="S1",
                criteria_overrides={"cost": 0.60},
            ),
        ]
        results = engine.run(supplier_decision, scenarios)
        assert "cost" in results[0].policy_delta
        assert results[0].policy_delta["cost"]["base"] == 0.25
        assert results[0].policy_delta["cost"]["scenario"] == 0.60

    def test_value_overrides(self, supplier_decision):
        engine = ScenarioEngine()
        scenarios = [
            Scenario(
                id="s1", name="S1",
                value_overrides={"a": {"compliance": 95}},
            ),
        ]
        results = engine.run(supplier_decision, scenarios)
        assert len(results) == 1
