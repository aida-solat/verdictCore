"""Tests for Evidence Quality analyzer."""

import pytest

from verdictcore import (
    Alternative,
    Criterion,
    DecisionInput,
    Deciwa,
    Evidence,
)
from verdictcore.evidence import EvidenceQualityAnalyzer


@pytest.fixture
def decision_with_evidence() -> DecisionInput:
    return DecisionInput(
        decision_id="test_eq_001",
        question="Which model?",
        domain="test",
        criteria=[
            Criterion(name="accuracy", weight=0.5, direction="maximize"),
            Criterion(name="speed", weight=0.5, direction="maximize"),
        ],
        alternatives=[
            Alternative(
                id="a", name="Model A",
                values={"accuracy": 92, "speed": 150},
            ),
            Alternative(
                id="b", name="Model B",
                values={"accuracy": 88, "speed": 200},
            ),
        ],
        evidence=[
            Evidence(
                id="ev1", alternative_id="a", field="accuracy",
                source="benchmark.pdf",
                source_type="official_document",
                claim="Benchmark shows 92% accuracy",
                value=92, confidence=0.95, reliability=0.92,
                freshness_days=30,
            ),
            Evidence(
                id="ev2", alternative_id="a", field="speed",
                source="vendor email",
                source_type="vendor_statement",
                claim="Vendor claims 150ms",
                value=150, confidence=0.60, reliability=0.55,
                freshness_days=None,
            ),
            Evidence(
                id="ev3", alternative_id="b", field="accuracy",
                source="internal test",
                source_type="manual_entry",
                claim="Internal test gave 88%",
                value=88, confidence=0.70, reliability=0.65,
                freshness_days=180,
            ),
        ],
    )


class TestEvidenceQuality:

    def test_basic_evaluation(self, decision_with_evidence):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_evidence)
        analyzer = EvidenceQualityAnalyzer()
        report = analyzer.evaluate(decision_with_evidence, result)

        assert 0.0 <= report.overall_evidence_quality <= 1.0
        assert report.level in ("high", "medium", "low", "unknown")
        assert len(report.field_scores) == 3

    def test_high_quality_evidence_scores_high(self, decision_with_evidence):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_evidence)
        analyzer = EvidenceQualityAnalyzer()
        report = analyzer.evaluate(decision_with_evidence, result)

        ev1_score = next(
            s for s in report.field_scores if s.evidence_id == "ev1"
        )
        assert ev1_score.overall_quality > 0.75
        assert ev1_score.level == "high"

    def test_vendor_statement_lower_than_official(self, decision_with_evidence):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_evidence)
        analyzer = EvidenceQualityAnalyzer()
        report = analyzer.evaluate(decision_with_evidence, result)

        ev1 = next(s for s in report.field_scores if s.evidence_id == "ev1")
        ev2 = next(s for s in report.field_scores if s.evidence_id == "ev2")
        assert ev1.overall_quality > ev2.overall_quality

    def test_no_evidence_returns_unknown(self):
        decision = DecisionInput(
            decision_id="test_eq_002",
            question="No evidence?",
            domain="test",
            criteria=[
                Criterion(name="score", weight=1.0, direction="maximize"),
            ],
            alternatives=[
                Alternative(id="a", name="A", values={"score": 90}),
            ],
        )
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision)
        analyzer = EvidenceQualityAnalyzer()
        report = analyzer.evaluate(decision, result)
        assert report.level == "unknown"
        assert report.overall_evidence_quality == 0.0

    def test_freshness_score_applied(self, decision_with_evidence):
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision_with_evidence)
        analyzer = EvidenceQualityAnalyzer()
        report = analyzer.evaluate(decision_with_evidence, result)

        ev1 = next(s for s in report.field_scores if s.evidence_id == "ev1")
        assert ev1.freshness_score == 1.0

        ev3 = next(s for s in report.field_scores if s.evidence_id == "ev3")
        assert ev3.freshness_score == 0.6

    def test_warnings_for_low_quality_winner(self):
        decision = DecisionInput(
            decision_id="test_eq_003",
            question="Low quality winner?",
            domain="test",
            criteria=[
                Criterion(name="score", weight=1.0, direction="maximize"),
            ],
            alternatives=[
                Alternative(id="a", name="A", values={"score": 90}),
            ],
            evidence=[
                Evidence(
                    id="ev_low", alternative_id="a", field="score",
                    source="random blog",
                    source_type="unknown",
                    claim="Guessed score",
                    confidence=0.2, reliability=0.2,
                    freshness_days=400,
                ),
            ],
        )
        engine = Deciwa(enable_sensitivity=False)
        result = engine.run(decision)
        analyzer = EvidenceQualityAnalyzer()
        report = analyzer.evaluate(decision, result)
        assert len(report.warnings) > 0
