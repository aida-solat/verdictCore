"""Tests for Decision Portfolio Simulation."""

from verdictcore import Alternative, Criterion, DecisionInput, Deciwa
from verdictcore.models.constraint import Constraint
from verdictcore.policies.model import DecisionPolicy
from verdictcore.portfolio import PortfolioSimulator


def _make_decision(decision_id: str) -> DecisionInput:
    return DecisionInput(
        decision_id=decision_id,
        question="Test?",
        domain="supplier_selection",
        criteria=[
            Criterion(name="cost", weight=0.40, direction="minimize"),
            Criterion(name="compliance", weight=0.30, direction="maximize"),
            Criterion(name="security", weight=0.30, direction="maximize"),
        ],
        constraints=[
            Constraint(field="security", operator=">=", value=75, action="block"),
        ],
        alternatives=[
            Alternative(
                id="a", name="A",
                values={"cost": 500, "compliance": 88, "security": 85},
            ),
            Alternative(
                id="b", name="B",
                values={"cost": 480, "compliance": 91, "security": 90},
            ),
            Alternative(
                id="c", name="C",
                values={"cost": 450, "compliance": 80, "security": 78},
            ),
        ],
    )


class TestPortfolioSimulator:

    def test_no_impact_same_policy(self):
        decisions = [_make_decision(f"d_{i}") for i in range(5)]
        engine = Deciwa(enable_sensitivity=False)
        results = [engine.run(d) for d in decisions]

        same_policy = DecisionPolicy(
            policy_id="same",
            version="v1",
            domain="supplier_selection",
            criteria=[
                Criterion(name="cost", weight=0.40, direction="minimize"),
                Criterion(name="compliance", weight=0.30, direction="maximize"),
                Criterion(name="security", weight=0.30, direction="maximize"),
            ],
            constraints=[
                Constraint(field="security", operator=">=", value=75, action="block"),
            ],
        )

        simulator = PortfolioSimulator()
        result = simulator.simulate_policy_impact(decisions, results, same_policy)

        assert result.decisions_analyzed == 5
        assert result.winner_changed_count == 0
        assert result.winner_changed_rate == 0.0

    def test_policy_change_causes_impact(self):
        decisions = [_make_decision(f"d_{i}") for i in range(5)]
        engine = Deciwa(enable_sensitivity=False)
        results = [engine.run(d) for d in decisions]

        new_policy = DecisionPolicy(
            policy_id="cost_heavy",
            version="v2",
            domain="supplier_selection",
            criteria=[
                Criterion(name="cost", weight=0.80, direction="minimize"),
                Criterion(name="compliance", weight=0.10, direction="maximize"),
                Criterion(name="security", weight=0.10, direction="maximize"),
            ],
            constraints=[
                Constraint(field="security", operator=">=", value=75, action="block"),
            ],
        )

        simulator = PortfolioSimulator()
        result = simulator.simulate_policy_impact(decisions, results, new_policy)

        assert result.decisions_analyzed == 5
        assert result.winner_changed_count > 0

    def test_empty_input(self):
        simulator = PortfolioSimulator()
        result = simulator.simulate_policy_impact(
            [], [],
            DecisionPolicy(
                policy_id="x", version="v1", domain="d",
                criteria=[],
            ),
        )
        assert result.decisions_analyzed == 0

    def test_recommendation_generated(self):
        decisions = [_make_decision(f"d_{i}") for i in range(5)]
        engine = Deciwa(enable_sensitivity=False)
        results = [engine.run(d) for d in decisions]

        policy = DecisionPolicy(
            policy_id="same",
            version="v1",
            domain="supplier_selection",
            criteria=[
                Criterion(name="cost", weight=0.40, direction="minimize"),
                Criterion(name="compliance", weight=0.30, direction="maximize"),
                Criterion(name="security", weight=0.30, direction="maximize"),
            ],
        )

        simulator = PortfolioSimulator()
        result = simulator.simulate_policy_impact(decisions, results, policy)
        assert result.recommendation != ""
