"""Tests for Value-of-Information analyzer."""

import pytest

from verdictcore import (
    Alternative,
    Constraint,
    Criterion,
    DecisionInput,
    Deciwa,
    Evidence,
)
from verdictcore.voi import ValueOfInformationAnalyzer


@pytest.fixture
def decision_with_missing() -> DecisionInput:
    return DecisionInput(
        decision_id="test_voi_001",
        question="Which supplier?",
        domain="test",
        criteria=[
            Criterion(name="cost", weight=0.30, direction="minimize"),
            Criterion(name="compliance", weight=0.40, direction="maximize"),
            Criterion(name="security", weight=0.30, direction="maximize"),
        ],
        constraints=[
            Constraint(
                field="compliance", operator=">=", value=85, action="block",
            ),
        ],
        alternatives=[
            Alternative(
                id="a", name="A",
                values={"cost": 500, "compliance": 90, "security": 88},
            ),
            Alternative(
                id="b", name="B",
                values={"cost": 450, "compliance": None, "security": 85},
            ),
        ],
        evidence=[
            Evidence(
                id="ev1", alternative_id="a", field="compliance",
                source="cert.pdf", claim="A has ISO cert", value=90,
                confidence=0.9, reliability=0.95,
            ),
        ],
    )


class TestValueOfInformation:

    def test_detects_missing_field(self, decision_with_missing):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_missing)
        analyzer = ValueOfInformationAnalyzer()
        report = analyzer.analyze(decision_with_missing, result)

        assert len(report.items) >= 1
        fields = {item.field for item in report.items}
        assert "compliance" in fields

    def test_missing_constraint_field_high_impact(self, decision_with_missing):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_missing)
        analyzer = ValueOfInformationAnalyzer()
        report = analyzer.analyze(decision_with_missing, result)

        compliance_items = [
            i for i in report.items
            if i.field == "compliance" and i.alternative_id == "b"
        ]
        assert len(compliance_items) == 1
        assert compliance_items[0].constraint_related is True
        assert compliance_items[0].estimated_impact > 0.0

    def test_impact_sorted_descending(self, decision_with_missing):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_missing)
        analyzer = ValueOfInformationAnalyzer()
        report = analyzer.analyze(decision_with_missing, result)

        impacts = [i.estimated_impact for i in report.items]
        assert impacts == sorted(impacts, reverse=True)

    def test_suggested_question_generated(self, decision_with_missing):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_missing)
        analyzer = ValueOfInformationAnalyzer()
        report = analyzer.analyze(decision_with_missing, result)

        for item in report.items:
            assert item.suggested_question
            assert len(item.suggested_question) > 10

    def test_no_missing_returns_empty(self):
        decision = DecisionInput(
            decision_id="test_voi_002",
            question="All complete?",
            domain="test",
            criteria=[
                Criterion(name="score", weight=1.0, direction="maximize"),
            ],
            alternatives=[
                Alternative(id="a", name="A", values={"score": 90}),
                Alternative(id="b", name="B", values={"score": 80}),
            ],
        )
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision)
        analyzer = ValueOfInformationAnalyzer()
        report = analyzer.analyze(decision, result)
        assert len(report.items) == 0

    def test_top_items_property(self, decision_with_missing):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_missing)
        analyzer = ValueOfInformationAnalyzer()
        report = analyzer.analyze(decision_with_missing, result)
        top = report.top_items
        if len(top) >= 2:
            assert top[0].estimated_impact >= top[1].estimated_impact
