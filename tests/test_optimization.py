"""Tests for Multi-Objective Optimization and Constraint Optimizer."""

import pytest

from verdictcore import Alternative, Criterion, DecisionInput
from verdictcore.models.constraint import Constraint
from verdictcore.optimization import ConstraintOptimizer, ParetoAnalyzer
from verdictcore.optimization.constraint_optimizer import ConstraintOptimizationInput
from verdictcore.optimization.objectives import Objective


@pytest.fixture
def alternatives() -> list[Alternative]:
    return [
        Alternative(
            id="a", name="A",
            values={"cost": 100, "compliance": 90, "delivery": 20},
        ),
        Alternative(
            id="b", name="B",
            values={"cost": 80, "compliance": 85, "delivery": 15},
        ),
        Alternative(
            id="c", name="C",
            values={"cost": 120, "compliance": 95, "delivery": 25},
        ),
        Alternative(
            id="d", name="D",
            values={"cost": 110, "compliance": 80, "delivery": 22},
        ),
    ]


@pytest.fixture
def objectives() -> list[Objective]:
    return [
        Objective(field="cost", direction="minimize"),
        Objective(field="compliance", direction="maximize"),
        Objective(field="delivery", direction="minimize"),
    ]


class TestParetoAnalyzer:

    def test_identifies_frontier(self, alternatives, objectives):
        analyzer = ParetoAnalyzer()
        report = analyzer.analyze("test_001", alternatives, objectives)

        frontier_ids = [p.alternative_id for p in report.pareto_frontier]
        assert "b" in frontier_ids
        assert len(report.pareto_frontier) >= 1

    def test_identifies_dominated(self, alternatives, objectives):
        analyzer = ParetoAnalyzer()
        report = analyzer.analyze("test_001", alternatives, objectives)

        dominated_ids = [d.alternative_id for d in report.dominated_alternatives]
        assert "d" in dominated_ids

    def test_single_dominant(self):
        alts = [
            Alternative(id="x", name="X", values={"a": 100, "b": 100}),
            Alternative(id="y", name="Y", values={"a": 50, "b": 50}),
        ]
        objs = [
            Objective(field="a", direction="maximize"),
            Objective(field="b", direction="maximize"),
        ]
        analyzer = ParetoAnalyzer()
        report = analyzer.analyze("test_002", alts, objs)

        assert len(report.pareto_frontier) == 1
        assert report.pareto_frontier[0].alternative_id == "x"

    def test_all_pareto(self):
        alts = [
            Alternative(id="x", name="X", values={"a": 100, "b": 50}),
            Alternative(id="y", name="Y", values={"a": 50, "b": 100}),
        ]
        objs = [
            Objective(field="a", direction="maximize"),
            Objective(field="b", direction="maximize"),
        ]
        analyzer = ParetoAnalyzer()
        report = analyzer.analyze("test_003", alts, objs)

        assert len(report.pareto_frontier) == 2

    def test_interpretation(self, alternatives, objectives):
        analyzer = ParetoAnalyzer()
        report = analyzer.analyze("test_004", alternatives, objectives)
        assert len(report.interpretation) >= 1


class TestConstraintOptimizer:

    def test_basic_optimization(self):
        decision = DecisionInput(
            decision_id="copt_001",
            question="Optimize compliance threshold",
            domain="test",
            criteria=[
                Criterion(name="cost", weight=0.5, direction="minimize"),
                Criterion(name="compliance", weight=0.5, direction="maximize"),
            ],
            constraints=[
                Constraint(
                    field="compliance", operator=">=",
                    value=80, action="block",
                ),
            ],
            alternatives=[
                Alternative(id="a", name="A", values={"cost": 100, "compliance": 88}),
                Alternative(id="b", name="B", values={"cost": 80, "compliance": 82}),
                Alternative(id="c", name="C", values={"cost": 70, "compliance": 78}),
            ],
        )
        opt_input = ConstraintOptimizationInput(
            field="compliance",
            operator=">=",
            candidate_values=[75, 80, 85, 90],
        )
        optimizer = ConstraintOptimizer()
        result = optimizer.optimize(decision, opt_input)

        assert result.field == "compliance"
        assert len(result.candidates) == 4
        assert result.recommended_threshold is not None

    def test_blocked_rate_increases(self):
        decision = DecisionInput(
            decision_id="copt_002",
            question="Test",
            domain="test",
            criteria=[
                Criterion(name="score", weight=1.0, direction="maximize"),
            ],
            constraints=[
                Constraint(
                    field="score", operator=">=",
                    value=50, action="block",
                ),
            ],
            alternatives=[
                Alternative(id="a", name="A", values={"score": 90}),
                Alternative(id="b", name="B", values={"score": 70}),
                Alternative(id="c", name="C", values={"score": 50}),
            ],
        )
        opt_input = ConstraintOptimizationInput(
            field="score",
            operator=">=",
            candidate_values=[50, 60, 80, 95],
        )
        optimizer = ConstraintOptimizer()
        result = optimizer.optimize(decision, opt_input)

        rates = [c.blocked_rate for c in result.candidates]
        assert rates[-1] >= rates[0]
