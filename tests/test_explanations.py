"""Tests for explanation generation."""

import pytest

from verdictcore import (
    Alternative,
    Constraint,
    Criterion,
    DecisionInput,
    Deciwa,
)


@pytest.fixture
def decision_with_clear_winner() -> DecisionInput:
    return DecisionInput(
        question="Clear winner test",
        domain="test",
        criteria=[
            Criterion(name="quality", weight=0.7, direction="maximize"),
            Criterion(name="cost", weight=0.3, direction="minimize"),
        ],
        constraints=[
            Constraint(field="quality", operator=">=", value=50, action="block"),
        ],
        alternatives=[
            Alternative(id="winner", name="Winner", values={"quality": 95, "cost": 30}),
            Alternative(id="loser", name="Loser", values={"quality": 60, "cost": 80}),
            Alternative(id="blocked", name="Blocked", values={"quality": 40, "cost": 10}),
        ],
    )


class TestExplanations:
    def test_why_selected_mentions_winner(self, decision_with_clear_winner):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_clear_winner)
        assert "Winner" in result.explanation.why_selected

    def test_why_not_blocked(self, decision_with_clear_winner):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_clear_winner)
        blocked_explanation = result.why_not("blocked")
        assert blocked_explanation is not None
        text = blocked_explanation.lower()
        assert "blocked" in text or "constraint" in text

    def test_why_not_lower_score(self, decision_with_clear_winner):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_clear_winner)
        loser_explanation = result.why_not("loser")
        assert loser_explanation is not None
        assert "score" in loser_explanation.lower() or "below" in loser_explanation.lower()

    def test_top_drivers_non_empty(self, decision_with_clear_winner):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_clear_winner)
        assert len(result.explanation.top_drivers) > 0
        # Top driver should be quality (weight 0.7)
        top = result.explanation.top_drivers[0]
        assert top.criterion == "quality"

    def test_why_not_returns_none_for_winner(self, decision_with_clear_winner):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_clear_winner)
        assert result.why_not("winner") is None
