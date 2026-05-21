"""Tests for the Deciwa."""

import pytest

from verdictcore import (
    Alternative,
    Constraint,
    Criterion,
    DecisionInput,
    DecisionResult,
    Deciwa,
)
from verdictcore.models.result import DecisionStatus


@pytest.fixture
def healthcare_decision() -> DecisionInput:
    """Healthcare AI model selection decision input."""
    return DecisionInput(
        decision_id="test_healthcare_001",
        question="Which AI model for healthcare RAG?",
        domain="ai_model_selection",
        criteria=[
            Criterion(name="accuracy", weight=0.35, direction="maximize"),
            Criterion(name="privacy", weight=0.25, direction="maximize"),
            Criterion(name="compliance", weight=0.25, direction="maximize"),
            Criterion(name="latency", weight=0.10, direction="minimize"),
            Criterion(name="cost", weight=0.05, direction="minimize"),
        ],
        constraints=[
            Constraint(field="privacy", operator=">=", value=85, action="block"),
            Constraint(field="compliance", operator=">=", value=90, action="block"),
        ],
        alternatives=[
            Alternative(
                id="model_a",
                name="Model A",
                values={
                    "accuracy": 88, "privacy": 70, "compliance": 75,
                    "latency": 220, "cost": 0.8,
                },
            ),
            Alternative(
                id="model_b",
                name="Model B",
                values={
                    "accuracy": 91, "privacy": 85, "compliance": 90,
                    "latency": 400, "cost": 0.5,
                },
            ),
            Alternative(
                id="model_c",
                name="Model C",
                values={
                    "accuracy": 82, "privacy": 95, "compliance": 95,
                    "latency": 150, "cost": 0.2,
                },
            ),
        ],
    )


@pytest.fixture
def engine() -> Deciwa:
    return Deciwa(enable_sensitivity=True)


class TestDeciwa:
    def test_basic_run(self, engine: Deciwa, healthcare_decision: DecisionInput):
        result = engine.run(healthcare_decision)
        assert isinstance(result, DecisionResult)
        assert result.decision_id == "test_healthcare_001"
        assert result.domain == "ai_model_selection"

    def test_model_a_blocked(self, engine: Deciwa, healthcare_decision: DecisionInput):
        """Model A should be blocked due to privacy and compliance constraints."""
        result = engine.run(healthcare_decision)
        blocked = [r for r in result.rankings if r.blocked]
        assert len(blocked) == 1
        assert blocked[0].alternative_id == "model_a"

    def test_winner_selected(self, engine: Deciwa, healthcare_decision: DecisionInput):
        """A winner should be selected from eligible alternatives."""
        result = engine.run(healthcare_decision)
        assert result.status == DecisionStatus.DECIDED
        assert result.recommendation.selected_alternative_id in ("model_b", "model_c")
        assert result.recommendation.confidence > 0.5

    def test_rankings_ordered(self, engine: Deciwa, healthcare_decision: DecisionInput):
        """Non-blocked alternatives should be ranked by score."""
        result = engine.run(healthcare_decision)
        eligible = [r for r in result.rankings if not r.blocked]
        for i in range(len(eligible) - 1):
            assert eligible[i].total_score >= eligible[i + 1].total_score

    def test_explanation_generated(self, engine: Deciwa, healthcare_decision: DecisionInput):
        result = engine.run(healthcare_decision)
        assert result.explanation.why_selected
        assert len(result.explanation.top_drivers) > 0
        assert len(result.explanation.why_not) > 0

    def test_audit_hashes_present(self, engine: Deciwa, healthcare_decision: DecisionInput):
        result = engine.run(healthcare_decision)
        assert result.audit.input_hash.startswith("sha256:")
        assert result.audit.ruleset_hash.startswith("sha256:")
        assert result.audit.output_hash.startswith("sha256:")

    def test_reproducibility(self, engine: Deciwa, healthcare_decision: DecisionInput):
        """Running the same input twice should produce the same hashes."""
        result1 = engine.run(healthcare_decision)
        result2 = engine.run(healthcare_decision)
        assert result1.audit.input_hash == result2.audit.input_hash
        assert result1.audit.ruleset_hash == result2.audit.ruleset_hash
        # Rankings should be identical
        assert (
            result1.recommendation.selected_alternative_id
            == result2.recommendation.selected_alternative_id
        )

    def test_all_blocked(self, engine: Deciwa):
        """When all alternatives are blocked, status should be BLOCKED."""
        decision = DecisionInput(
            question="All fail?",
            domain="test",
            criteria=[Criterion(name="score", weight=1.0, direction="maximize")],
            constraints=[Constraint(field="score", operator=">=", value=100, action="block")],
            alternatives=[
                Alternative(id="a", name="A", values={"score": 50}),
                Alternative(id="b", name="B", values={"score": 60}),
            ],
        )
        result = engine.run(decision)
        assert result.status == DecisionStatus.BLOCKED
        assert result.recommendation.decision_class == "reject"

    def test_no_constraints(self, engine: Deciwa):
        """Decision should work without any constraints."""
        decision = DecisionInput(
            question="Simple choice",
            domain="test",
            criteria=[
                Criterion(name="quality", weight=0.6, direction="maximize"),
                Criterion(name="cost", weight=0.4, direction="minimize"),
            ],
            alternatives=[
                Alternative(id="a", name="A", values={"quality": 80, "cost": 100}),
                Alternative(id="b", name="B", values={"quality": 90, "cost": 50}),
            ],
        )
        result = engine.run(decision)
        assert result.status == DecisionStatus.DECIDED
        assert result.recommendation.selected_alternative_id == "b"

    def test_canonical_json_output(self, engine: Deciwa, healthcare_decision: DecisionInput):
        result = engine.run(healthcare_decision)
        json_str = result.to_canonical_json()
        assert "decision_id" in json_str
        assert "test_healthcare_001" in json_str

    def test_sensitivity_analysis_present(self, engine: Deciwa, healthcare_decision: DecisionInput):
        result = engine.run(healthcare_decision)
        assert result.explanation.sensitivity is not None
        assert result.explanation.sensitivity.decision_stability_score >= 0
        assert result.explanation.sensitivity.decision_stability_score <= 1
        valid_levels = ("stable", "moderately_stable", "fragile", "unstable")
        assert result.explanation.sensitivity.level in valid_levels
