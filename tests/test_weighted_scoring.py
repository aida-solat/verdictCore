"""Tests for weighted scoring logic."""

import pytest

from verdictcore.models.alternative import Alternative
from verdictcore.models.criterion import Criterion
from verdictcore.models.policy import MissingPolicy
from verdictcore.scoring.weighted import WeightedScorer


@pytest.fixture
def simple_criteria() -> list[Criterion]:
    return [
        Criterion(name="speed", weight=0.5, direction="maximize"),
        Criterion(name="cost", weight=0.5, direction="minimize"),
    ]


@pytest.fixture
def simple_alternatives() -> list[Alternative]:
    return [
        Alternative(id="a", name="A", values={"speed": 100, "cost": 50}),
        Alternative(id="b", name="B", values={"speed": 80, "cost": 30}),
        Alternative(id="c", name="C", values={"speed": 60, "cost": 80}),
    ]


class TestWeightedScorer:
    def test_basic_scoring(self, simple_criteria, simple_alternatives):
        scorer = WeightedScorer(simple_criteria, simple_alternatives)
        traces = scorer.score()
        assert len(traces) == 3
        # Each trace should have total_score > 0
        for t in traces:
            assert t.total_score >= 0

    def test_maximize_direction(self, simple_criteria, simple_alternatives):
        """Higher speed should give higher normalized score for maximize."""
        scorer = WeightedScorer(simple_criteria, simple_alternatives)
        traces = scorer.score()
        # A has speed 100 (highest) → normalized 1.0
        a_trace = next(t for t in traces if t.alternative_id == "a")
        assert a_trace.criteria["speed"].normalized == 1.0

    def test_minimize_direction(self, simple_criteria, simple_alternatives):
        """Lower cost should give higher normalized score for minimize."""
        scorer = WeightedScorer(simple_criteria, simple_alternatives)
        traces = scorer.score()
        # B has cost 30 (lowest) → normalized 1.0
        b_trace = next(t for t in traces if t.alternative_id == "b")
        assert b_trace.criteria["cost"].normalized == 1.0

    def test_all_same_values(self):
        """When all values are the same, normalized should be 1.0."""
        criteria = [Criterion(name="x", weight=1.0, direction="maximize")]
        alternatives = [
            Alternative(id="a", name="A", values={"x": 50}),
            Alternative(id="b", name="B", values={"x": 50}),
        ]
        scorer = WeightedScorer(criteria, alternatives)
        traces = scorer.score()
        assert traces[0].criteria["x"].normalized == 1.0
        assert traces[1].criteria["x"].normalized == 1.0

    def test_missing_data_flagged(self):
        """Missing values should be detected."""
        criteria = [Criterion(name="x", weight=1.0, direction="maximize")]
        alternatives = [
            Alternative(id="a", name="A", values={"x": 50}),
            Alternative(id="b", name="B", values={}),
        ]
        scorer = WeightedScorer(criteria, alternatives, MissingPolicy.NEEDS_REVIEW)
        traces = scorer.score()
        assert scorer.has_missing_data is True
        b_trace = next(t for t in traces if t.alternative_id == "b")
        assert b_trace.criteria["x"].normalized is None

    def test_penalize_missing(self):
        """Missing values with penalize policy should give 0 contribution."""
        criteria = [Criterion(name="x", weight=1.0, direction="maximize")]
        alternatives = [
            Alternative(id="a", name="A", values={"x": 50}),
            Alternative(id="b", name="B", values={}),
        ]
        scorer = WeightedScorer(criteria, alternatives, MissingPolicy.PENALIZE)
        traces = scorer.score()
        b_trace = next(t for t in traces if t.alternative_id == "b")
        assert b_trace.total_score == 0.0

    def test_score_range(self, simple_criteria, simple_alternatives):
        """Scores should be between 0 and 100."""
        scorer = WeightedScorer(simple_criteria, simple_alternatives)
        traces = scorer.score()
        for t in traces:
            assert 0 <= t.total_score <= 100
