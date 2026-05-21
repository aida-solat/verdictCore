"""Tests for sensitivity analysis."""

import pytest

from verdictcore import Alternative, Criterion, DecisionInput, Deciwa


@pytest.fixture
def tight_decision() -> DecisionInput:
    """Decision where alternatives are very close — should be fragile."""
    return DecisionInput(
        question="Tight race",
        domain="test",
        criteria=[
            Criterion(name="a", weight=0.5, direction="maximize"),
            Criterion(name="b", weight=0.5, direction="maximize"),
        ],
        alternatives=[
            Alternative(id="x", name="X", values={"a": 80, "b": 81}),
            Alternative(id="y", name="Y", values={"a": 81, "b": 80}),
        ],
    )


@pytest.fixture
def dominant_decision() -> DecisionInput:
    """Decision with a clearly dominant winner — should be stable."""
    return DecisionInput(
        question="Clear dominance",
        domain="test",
        criteria=[
            Criterion(name="a", weight=0.5, direction="maximize"),
            Criterion(name="b", weight=0.5, direction="maximize"),
        ],
        alternatives=[
            Alternative(id="x", name="X", values={"a": 95, "b": 95}),
            Alternative(id="y", name="Y", values={"a": 30, "b": 30}),
        ],
    )


class TestSensitivity:
    def test_sensitivity_returns_result(self, tight_decision):
        engine = Deciwa(enable_sensitivity=True)
        result = engine.run(tight_decision)
        assert result.explanation.sensitivity is not None

    def test_tight_race_is_not_stable(self, tight_decision):
        engine = Deciwa(enable_sensitivity=True)
        result = engine.run(tight_decision)
        sens = result.explanation.sensitivity
        assert sens is not None
        # Very close alternatives should not be "stable"
        assert sens.level in ("fragile", "unstable", "moderately_stable")

    def test_dominant_is_stable(self, dominant_decision):
        engine = Deciwa(enable_sensitivity=True)
        result = engine.run(dominant_decision)
        sens = result.explanation.sensitivity
        assert sens is not None
        assert sens.level == "stable"
        assert sens.decision_stability_score >= 0.85

    def test_sensitivity_disabled(self, tight_decision):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(tight_decision)
        assert result.explanation.sensitivity is None

    def test_winner_changes_if_populated(self, tight_decision):
        engine = Deciwa(enable_sensitivity=True)
        result = engine.run(tight_decision)
        sens = result.explanation.sensitivity
        assert sens is not None
        if sens.sensitive_to:
            assert len(sens.winner_changes_if) > 0
