"""Tests for Governance Pack."""

from verdictcore import Alternative, Criterion, DecisionInput, Deciwa
from verdictcore.governance import GovernanceEngine
from verdictcore.governance.engine import GovernanceRule
from verdictcore.models.intelligence import RobustnessReport


def _make_result(spend: int = 0):
    decision = DecisionInput(
        decision_id="gov_test_001",
        question="Which?",
        domain="test",
        criteria=[
            Criterion(name="score", weight=1.0, direction="maximize"),
        ],
        alternatives=[
            Alternative(id="a", name="A", values={"score": 90}),
            Alternative(id="b", name="B", values={"score": 80}),
        ],
        metadata={"spend": spend},
    )
    return Deciwa(enable_sensitivity=False).run(decision)


class TestGovernance:

    def test_no_rules_no_actions(self):
        result = _make_result()
        engine = GovernanceEngine()
        report = engine.evaluate(result)

        assert report.decision_id == "gov_test_001"
        assert report.review_required is False
        assert report.approval_required is False
        assert report.blocked is False

    def test_spend_threshold_triggers(self):
        result = _make_result(spend=2_000_000)
        rules = [
            GovernanceRule(
                id="high_spend",
                name="High Spend",
                condition="metadata.get('spend', 0) >= 1000000",
                action="require_approval",
                message="Spend exceeds 1M threshold.",
            ),
        ]
        engine = GovernanceEngine(rules=rules)
        report = engine.evaluate(result)

        assert report.approval_required is True
        assert len(report.actions) == 1
        assert report.actions[0].rule_id == "high_spend"

    def test_robustness_rule(self):
        result = _make_result()
        robustness = RobustnessReport(
            decision_id="gov_test_001",
            stability_score=0.4,
            scenario_consistency_score=0.3,
            data_completeness_score=0.8,
            evidence_quality_score=0.5,
            constraint_risk_score=0.6,
            overall_robustness_score=0.4,
            level="weak",
        )
        rules = [
            GovernanceRule(
                id="weak_robustness",
                name="Weak Robustness",
                condition=(
                    "robustness.get('level') in ['weak', 'fragile']"
                ),
                action="require_review",
                message="Decision robustness is weak.",
            ),
        ]
        engine = GovernanceEngine(rules=rules)
        report = engine.evaluate(result, robustness=robustness)

        assert report.review_required is True
        assert "weak" in report.reasons[0].lower()

    def test_risk_assessment_high_spend(self):
        result = _make_result(spend=1_500_000)
        robustness = RobustnessReport(
            decision_id="gov_test_001",
            stability_score=0.4,
            scenario_consistency_score=0.3,
            data_completeness_score=0.8,
            evidence_quality_score=0.5,
            constraint_risk_score=0.6,
            overall_robustness_score=0.4,
            level="weak",
        )
        engine = GovernanceEngine()
        report = engine.evaluate(result, robustness=robustness)
        assert report.risk_level in ("high", "critical")

    def test_from_rules_factory(self):
        rules_data = [
            {
                "id": "r1",
                "name": "Test Rule",
                "condition": "True",
                "action": "add_warning",
                "message": "Always triggered.",
            },
        ]
        engine = GovernanceEngine.from_rules(rules_data)
        result = _make_result()
        report = engine.evaluate(result)
        assert len(report.actions) == 1

    def test_block_action(self):
        result = _make_result()
        rules = [
            GovernanceRule(
                id="block_all",
                name="Block All",
                condition="True",
                action="block",
                message="Blocked by policy.",
            ),
        ]
        engine = GovernanceEngine(rules=rules)
        report = engine.evaluate(result)
        assert report.blocked is True
