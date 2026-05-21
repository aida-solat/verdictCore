"""Tests for Cross-Domain Transfer Lite."""

from verdictcore.patterns.discovery import DecisionPattern
from verdictcore.transfer import TransferAnalyzer


class TestTransferAnalyzer:

    def test_basic_transfer(self):
        source_patterns = [
            DecisionPattern(
                id="pat_fragility_high",
                domain="supplier_selection",
                pattern_type="fragility_pattern",
                description="High fragility rate.",
                confidence=0.8,
                support_count=30,
                recommendation_hint="Require review below 0.65.",
            ),
        ]
        analyzer = TransferAnalyzer()
        report = analyzer.analyze(
            source_patterns, target_domain="ai_model_selection",
        )
        assert len(report.candidates) >= 1
        assert report.candidates[0].target_domain == "ai_model_selection"

    def test_empty_patterns(self):
        analyzer = TransferAnalyzer()
        report = analyzer.analyze([], target_domain="test")
        assert report.candidates == []

    def test_confidence_is_bounded(self):
        source_patterns = [
            DecisionPattern(
                id="pat_1",
                domain="source",
                pattern_type="fragility_pattern",
                description="Test",
                confidence=0.9,
                support_count=50,
            ),
        ]
        analyzer = TransferAnalyzer()
        report = analyzer.analyze(source_patterns, target_domain="target")

        for c in report.candidates:
            assert 0 <= c.transfer_confidence <= 1.0
            assert c.risk in ("low", "medium", "high")

    def test_sorted_by_confidence(self):
        source_patterns = [
            DecisionPattern(
                id="pat_1", domain="source",
                pattern_type="fragility_pattern",
                description="1", confidence=0.5, support_count=10,
            ),
            DecisionPattern(
                id="pat_2", domain="source",
                pattern_type="constraint_failure_pattern",
                description="2", confidence=0.9, support_count=50,
            ),
        ]
        analyzer = TransferAnalyzer()
        report = analyzer.analyze(source_patterns, target_domain="target")

        if len(report.candidates) >= 2:
            assert (
                report.candidates[0].transfer_confidence
                >= report.candidates[1].transfer_confidence
            )
