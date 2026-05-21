"""Tests for Adaptive Policy Suggestions."""

from verdictcore.adaptive import AdaptiveSuggester
from verdictcore.drift.detector import DriftReport, DriftSignal
from verdictcore.patterns.discovery import DecisionPattern, PatternReport


class TestAdaptiveSuggester:

    def test_from_patterns(self):
        patterns = PatternReport(
            domain="test",
            decisions_analyzed=20,
            patterns=[
                DecisionPattern(
                    id="pat_fragility_high",
                    domain="test",
                    pattern_type="fragility_pattern",
                    description="50% fragile",
                    confidence=0.8,
                    support_count=10,
                ),
            ],
        )
        suggester = AdaptiveSuggester()
        report = suggester.suggest(pattern_report=patterns, policy_id="p1")

        assert len(report.suggestions) == 1
        assert report.suggestions[0].requires_human_approval is True
        assert report.all_require_approval is True

    def test_from_drift(self):
        drift = DriftReport(
            policy_id="p1",
            signals=[
                DriftSignal(
                    id="drift_001",
                    drift_type="outcome_drift",
                    severity="high",
                    description="Poor outcomes increased.",
                    confidence=0.75,
                    recommended_action="Strengthen evidence.",
                ),
            ],
            overall_drift_level="high",
        )
        suggester = AdaptiveSuggester()
        report = suggester.suggest(drift_report=drift, policy_id="p1")

        assert len(report.suggestions) == 1
        assert report.suggestions[0].suggestion_type == "change_evidence_requirement"

    def test_combined(self):
        patterns = PatternReport(
            domain="test",
            decisions_analyzed=20,
            patterns=[
                DecisionPattern(
                    id="pat_constraint_score",
                    domain="test",
                    pattern_type="constraint_failure_pattern",
                    description="score constraint fails often.",
                    confidence=0.7,
                    support_count=8,
                ),
            ],
        )
        drift = DriftReport(
            policy_id="p1",
            signals=[
                DriftSignal(
                    id="drift_c",
                    drift_type="constraint_drift",
                    severity="medium",
                    description="Blocked rate increased.",
                    confidence=0.6,
                ),
            ],
        )
        suggester = AdaptiveSuggester()
        report = suggester.suggest(
            pattern_report=patterns, drift_report=drift, policy_id="p1",
        )
        assert len(report.suggestions) == 2

    def test_empty_input(self):
        suggester = AdaptiveSuggester()
        report = suggester.suggest()
        assert report.suggestions == []
