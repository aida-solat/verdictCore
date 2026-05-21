"""Tests for Pattern Discovery."""

from verdictcore import Alternative, Criterion, DecisionInput, Deciwa
from verdictcore.models.constraint import Constraint
from verdictcore.patterns import PatternDiscovery


def _make_fragile_results(count: int = 10):
    results = []
    for i in range(count):
        decision = DecisionInput(
            decision_id=f"pat_{i}",
            question="Test?",
            domain="test_domain",
            criteria=[
                Criterion(name="score", weight=1.0, direction="maximize"),
            ],
            alternatives=[
                Alternative(id="a", name="A", values={"score": 50}),
            ],
        )
        results.append(Deciwa(enable_sensitivity=False).run(decision))
    return results


def _make_constraint_failure_results(count: int = 10):
    results = []
    for i in range(count):
        decision = DecisionInput(
            decision_id=f"cf_{i}",
            question="Test?",
            domain="test_domain",
            criteria=[
                Criterion(name="score", weight=1.0, direction="maximize"),
            ],
            constraints=[
                Constraint(field="score", operator=">=", value=80, action="block"),
            ],
            alternatives=[
                Alternative(id="a", name="A", values={"score": 70}),
                Alternative(id="b", name="B", values={"score": 90}),
            ],
        )
        results.append(Deciwa(enable_sensitivity=False).run(decision))
    return results


class TestPatternDiscovery:

    def test_empty_results(self):
        discovery = PatternDiscovery()
        report = discovery.discover([])
        assert report.decisions_analyzed == 0

    def test_constraint_failure_detected(self):
        results = _make_constraint_failure_results(10)
        discovery = PatternDiscovery()
        report = discovery.discover(results, domain="test_domain")

        assert report.decisions_analyzed == 10
        types = [p.pattern_type for p in report.patterns]
        assert "constraint_failure_pattern" in types

    def test_domain_filter(self):
        results = _make_constraint_failure_results(10)
        discovery = PatternDiscovery()
        report = discovery.discover(results, domain="other_domain")
        assert report.decisions_analyzed == 0

    def test_pattern_has_recommendation(self):
        results = _make_constraint_failure_results(10)
        discovery = PatternDiscovery()
        report = discovery.discover(results, domain="test_domain")

        for p in report.patterns:
            assert p.recommendation_hint is not None
