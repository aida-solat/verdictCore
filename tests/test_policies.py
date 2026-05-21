"""Tests for Policy Versioning & Diff."""

import pytest

from verdictcore.models.constraint import Constraint
from verdictcore.models.criterion import Criterion
from verdictcore.policies import DecisionPolicy, diff_policies


@pytest.fixture
def policy_v1() -> DecisionPolicy:
    return DecisionPolicy(
        policy_id="supplier_policy",
        version="v1",
        domain="supplier_selection",
        criteria=[
            Criterion(name="cost", weight=0.30, direction="minimize"),
            Criterion(name="compliance", weight=0.25, direction="maximize"),
            Criterion(name="security", weight=0.25, direction="maximize"),
            Criterion(name="delivery", weight=0.20, direction="minimize"),
        ],
        constraints=[
            Constraint(field="security", operator=">=", value=75, action="block"),
        ],
    )


@pytest.fixture
def policy_v2() -> DecisionPolicy:
    return DecisionPolicy(
        policy_id="supplier_policy",
        version="v2",
        domain="supplier_selection",
        criteria=[
            Criterion(name="cost", weight=0.20, direction="minimize"),
            Criterion(name="compliance", weight=0.35, direction="maximize"),
            Criterion(name="security", weight=0.25, direction="maximize"),
            Criterion(name="delivery", weight=0.10, direction="minimize"),
            Criterion(name="support", weight=0.10, direction="maximize"),
        ],
        constraints=[
            Constraint(field="security", operator=">=", value=80, action="block"),
            Constraint(field="compliance", operator=">=", value=85, action="block"),
        ],
    )


class TestPolicyDiff:

    def test_detect_weight_changes(self, policy_v1, policy_v2):
        diff = diff_policies(policy_v1, policy_v2)
        weight_changes = [
            c for c in diff.criteria_changes if c.field == "weight"
        ]
        assert len(weight_changes) >= 2
        cost_change = next(c for c in weight_changes if c.criterion == "cost")
        assert cost_change.from_value == 0.30
        assert cost_change.to_value == 0.20

    def test_detect_added_criterion(self, policy_v1, policy_v2):
        diff = diff_policies(policy_v1, policy_v2)
        added = [c for c in diff.criteria_changes if c.field == "added"]
        names = [c.criterion for c in added]
        assert "support" in names

    def test_detect_constraint_changes(self, policy_v1, policy_v2):
        diff = diff_policies(policy_v1, policy_v2)
        assert len(diff.constraint_changes) >= 1
        modified = [
            c for c in diff.constraint_changes if c.change_type == "modified"
        ]
        assert len(modified) >= 1

    def test_detect_added_constraint(self, policy_v1, policy_v2):
        diff = diff_policies(policy_v1, policy_v2)
        added = [
            c for c in diff.constraint_changes if c.change_type == "added"
        ]
        assert len(added) >= 1

    def test_interpretation_generated(self, policy_v1, policy_v2):
        diff = diff_policies(policy_v1, policy_v2)
        assert len(diff.interpretation) > 0

    def test_no_diff_same_policy(self, policy_v1):
        diff = diff_policies(policy_v1, policy_v1)
        assert diff.criteria_changes == []
        assert diff.constraint_changes == []

    def test_policy_properties(self, policy_v1):
        assert "cost" in policy_v1.weight_map
        assert policy_v1.weight_map["cost"] == 0.30
        assert "cost" in policy_v1.criteria_map
