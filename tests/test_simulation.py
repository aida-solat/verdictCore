"""Tests for Monte Carlo Simulation Engine."""

import random

import pytest

from verdictcore import Alternative, Criterion, DecisionInput
from verdictcore.simulation import SimulationEngine, SimulationVariable
from verdictcore.simulation.distributions import sample_variable
from verdictcore.simulation.variables import SimulationConfig


@pytest.fixture
def supplier_decision() -> DecisionInput:
    return DecisionInput(
        decision_id="sim_test_001",
        question="Which supplier under uncertainty?",
        domain="supplier_selection",
        criteria=[
            Criterion(name="cost", weight=0.40, direction="minimize"),
            Criterion(name="delivery", weight=0.30, direction="minimize"),
            Criterion(name="compliance", weight=0.30, direction="maximize"),
        ],
        alternatives=[
            Alternative(
                id="a", name="A",
                values={"cost": 500000, "delivery": 15, "compliance": 88},
            ),
            Alternative(
                id="b", name="B",
                values={"cost": 520000, "delivery": 12, "compliance": 91},
            ),
        ],
    )


@pytest.fixture
def sim_variables() -> list[SimulationVariable]:
    return [
        SimulationVariable(
            field="cost", alternative_id="a",
            distribution="normal",
            parameters={"mean": 500000, "std": 50000},
            bounds={"min": 350000, "max": 700000},
        ),
        SimulationVariable(
            field="cost", alternative_id="b",
            distribution="normal",
            parameters={"mean": 520000, "std": 30000},
            bounds={"min": 400000, "max": 650000},
        ),
        SimulationVariable(
            field="delivery", alternative_id="a",
            distribution="triangular",
            parameters={"min": 8, "mode": 15, "max": 35},
        ),
        SimulationVariable(
            field="delivery", alternative_id="b",
            distribution="triangular",
            parameters={"min": 5, "mode": 12, "max": 25},
        ),
    ]


class TestDistributions:

    def test_fixed(self):
        var = SimulationVariable(
            field="x", distribution="fixed",
            parameters={"value": 42},
        )
        rng = random.Random(1)
        assert sample_variable(var, rng) == 42.0

    def test_normal_bounded(self):
        var = SimulationVariable(
            field="x", distribution="normal",
            parameters={"mean": 100, "std": 50},
            bounds={"min": 50, "max": 150},
        )
        rng = random.Random(1)
        for _ in range(100):
            val = sample_variable(var, rng)
            assert 50 <= val <= 150

    def test_triangular(self):
        var = SimulationVariable(
            field="x", distribution="triangular",
            parameters={"min": 5, "mode": 10, "max": 30},
        )
        rng = random.Random(1)
        for _ in range(100):
            val = sample_variable(var, rng)
            assert 5 <= val <= 30

    def test_uniform(self):
        var = SimulationVariable(
            field="x", distribution="uniform",
            parameters={"min": 0, "max": 1},
        )
        rng = random.Random(1)
        for _ in range(100):
            val = sample_variable(var, rng)
            assert 0 <= val <= 1

    def test_beta(self):
        var = SimulationVariable(
            field="x", distribution="beta",
            parameters={"alpha": 2, "beta": 5},
        )
        rng = random.Random(1)
        for _ in range(100):
            val = sample_variable(var, rng)
            assert 0 <= val <= 1

    def test_categorical(self):
        var = SimulationVariable(
            field="x", distribution="categorical",
            parameters={"values": {"low": 0.5, "medium": 0.3, "high": 0.2}},
        )
        rng = random.Random(1)
        val = sample_variable(var, rng)
        assert val in ("low", "medium", "high")


class TestSimulationEngine:

    def test_basic_simulation(self, supplier_decision, sim_variables):
        engine = SimulationEngine()
        result = engine.run(
            supplier_decision,
            variables=sim_variables,
            iterations=500,
            seed=42,
        )
        assert result.decision_id == "sim_test_001"
        assert result.iterations == 500
        assert len(result.winner_distribution) >= 1
        assert result.selected_alternative is not None

    def test_reproducible_with_seed(self, supplier_decision, sim_variables):
        engine = SimulationEngine()
        r1 = engine.run(supplier_decision, variables=sim_variables, iterations=200, seed=42)
        r2 = engine.run(supplier_decision, variables=sim_variables, iterations=200, seed=42)

        assert r1.winner_distribution == r2.winner_distribution
        assert r1.selected_alternative == r2.selected_alternative

    def test_winner_distribution_sums_to_one(self, supplier_decision, sim_variables):
        engine = SimulationEngine()
        result = engine.run(
            supplier_decision, variables=sim_variables,
            iterations=1000, seed=42,
        )
        total = sum(w.win_rate for w in result.winner_distribution)
        assert abs(total - 1.0) < 0.01

    def test_risk_metrics_produced(self, supplier_decision, sim_variables):
        engine = SimulationEngine()
        result = engine.run(
            supplier_decision, variables=sim_variables,
            iterations=500, seed=42,
        )
        assert len(result.risk_metrics) >= 2
        for rm in result.risk_metrics:
            assert "cost" in rm.expected_values

    def test_interpretation_generated(self, supplier_decision, sim_variables):
        engine = SimulationEngine()
        result = engine.run(
            supplier_decision, variables=sim_variables,
            iterations=500, seed=42,
        )
        assert len(result.interpretation) >= 1

    def test_with_config(self, supplier_decision, sim_variables):
        config = SimulationConfig(
            iterations=100, seed=7, variables=sim_variables,
        )
        engine = SimulationEngine()
        result = engine.run(supplier_decision, config=config)
        assert result.iterations == 100
