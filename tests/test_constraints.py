"""Tests for constraint evaluation."""

import pytest

from verdictcore.constraints.evaluator import ConstraintEvaluator
from verdictcore.models.alternative import Alternative
from verdictcore.models.constraint import Constraint


@pytest.fixture
def alternatives() -> list[Alternative]:
    return [
        Alternative(id="a", name="A", values={"score": 90, "cost": 100}),
        Alternative(id="b", name="B", values={"score": 70, "cost": 200}),
        Alternative(id="c", name="C", values={"score": 85, "cost": 150}),
    ]


class TestConstraintEvaluator:
    def test_block_constraint(self, alternatives):
        constraints = [Constraint(field="score", operator=">=", value=80, action="block")]
        evaluator = ConstraintEvaluator(constraints, alternatives)
        results = evaluator.evaluate()
        blocked = evaluator.get_blocked_ids(results)
        assert "b" in blocked
        assert "a" not in blocked
        assert "c" not in blocked

    def test_warn_constraint(self, alternatives):
        constraints = [
            Constraint(field="cost", operator="<=", value=150, action="warn", message="Over budget")
        ]
        evaluator = ConstraintEvaluator(constraints, alternatives)
        results = evaluator.evaluate()
        warnings = evaluator.get_warnings_map(results)
        assert "b" in warnings
        assert "Over budget" in warnings["b"][0]

    def test_escalate_constraint(self, alternatives):
        constraints = [Constraint(field="cost", operator=">=", value=200, action="escalate")]
        evaluator = ConstraintEvaluator(constraints, alternatives)
        results = evaluator.evaluate()
        escalated = evaluator.get_escalation_ids(results)
        # a and c have cost < 200, so they fail the >= 200 check → escalated
        assert "a" in escalated
        assert "c" in escalated

    def test_operators(self):
        alt = [Alternative(id="x", name="X", values={"v": 50})]

        def check(op, val):
            ev = ConstraintEvaluator(
                [Constraint(field="v", operator=op, value=val, action="block")], alt
            )
            return ev.evaluate()[0].passed

        assert check(">", 40) is True
        assert check(">", 50) is False
        assert check("<", 60) is True
        assert check("==", 50) is True
        assert check("!=", 50) is False

    def test_missing_value_fails_constraint(self):
        alt = [Alternative(id="x", name="X", values={})]
        constraints = [Constraint(field="score", operator=">=", value=80, action="block")]
        evaluator = ConstraintEvaluator(constraints, alt)
        results = evaluator.evaluate()
        assert results[0].passed is False

    def test_in_operator(self):
        alt = [Alternative(id="x", name="X", values={"region": "eu"})]
        constraints = [Constraint(
            field="region", operator="in", value=["eu", "us"], action="block",
        )]
        evaluator = ConstraintEvaluator(constraints, alt)
        results = evaluator.evaluate()
        assert results[0].passed is True

    def test_not_in_operator(self):
        alt = [Alternative(id="x", name="X", values={"region": "cn"})]
        constraints = [Constraint(
            field="region", operator="not_in",
            value=["eu", "us"], action="block",
        )]
        evaluator = ConstraintEvaluator(constraints, alt)
        results = evaluator.evaluate()
        assert results[0].passed is True
