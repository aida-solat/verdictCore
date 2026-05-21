"""Tests for Decision Memory."""

from verdictcore import Alternative, Criterion, DecisionInput, Deciwa
from verdictcore.memory import DecisionMemory


def _make_results(count: int = 10):
    results = []
    for i in range(count):
        decision = DecisionInput(
            decision_id=f"mem_{i}",
            question="Test?",
            domain="supplier_selection",
            criteria=[
                Criterion(name="cost", weight=0.5, direction="minimize"),
                Criterion(name="quality", weight=0.5, direction="maximize"),
            ],
            alternatives=[
                Alternative(id="a", name="A", values={"cost": 100, "quality": 90}),
                Alternative(id="b", name="B", values={"cost": 80, "quality": 75}),
            ],
        )
        results.append(Deciwa(enable_sensitivity=False).run(decision))
    return results


class TestDecisionMemory:

    def test_summarize_basic(self):
        results = _make_results(10)
        memory = DecisionMemory(results)
        summary = memory.summarize(domain="supplier_selection")

        assert summary.decisions_analyzed == 10
        assert len(summary.most_common_winners) >= 1
        assert summary.domain == "supplier_selection"

    def test_empty_results(self):
        memory = DecisionMemory([])
        summary = memory.summarize()
        assert summary.decisions_analyzed == 0

    def test_status_distribution(self):
        results = _make_results(5)
        memory = DecisionMemory(results)
        summary = memory.summarize()
        assert "decided" in summary.status_distribution

    def test_domain_filter(self):
        results = _make_results(5)
        memory = DecisionMemory(results)
        summary = memory.summarize(domain="nonexistent")
        assert summary.decisions_analyzed == 0
