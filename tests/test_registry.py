"""Tests for Decision Registry (SQLite)."""

import tempfile

import pytest

from verdictcore import Alternative, Criterion, DecisionInput, Deciwa
from verdictcore.models.intelligence import OutcomeRecord
from verdictcore.registry import SQLiteDecisionRegistry
from verdictcore.registry.store import DecisionQuery


@pytest.fixture
def tmp_db():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        yield f.name


@pytest.fixture
def sample_result():
    decision = DecisionInput(
        decision_id="reg_test_001",
        question="Which?",
        domain="test_domain",
        criteria=[
            Criterion(name="score", weight=1.0, direction="maximize"),
        ],
        alternatives=[
            Alternative(id="a", name="A", values={"score": 90}),
            Alternative(id="b", name="B", values={"score": 80}),
        ],
    )
    engine = Deciwa(enable_sensitivity=False)
    return engine.run(decision)


class TestSQLiteRegistry:

    def test_save_and_get_run(self, tmp_db, sample_result):
        registry = SQLiteDecisionRegistry(tmp_db)
        registry.save_run(sample_result)

        loaded = registry.get_run("reg_test_001")
        assert loaded is not None
        assert loaded.decision_id == "reg_test_001"
        assert loaded.domain == "test_domain"
        registry.close()

    def test_list_runs(self, tmp_db, sample_result):
        registry = SQLiteDecisionRegistry(tmp_db)
        registry.save_run(sample_result)

        runs = registry.list_runs()
        assert len(runs) == 1
        registry.close()

    def test_list_runs_with_filter(self, tmp_db, sample_result):
        registry = SQLiteDecisionRegistry(tmp_db)
        registry.save_run(sample_result)

        query = DecisionQuery(domain="test_domain")
        runs = registry.list_runs(query)
        assert len(runs) == 1

        query = DecisionQuery(domain="nonexistent")
        runs = registry.list_runs(query)
        assert len(runs) == 0
        registry.close()

    def test_get_nonexistent(self, tmp_db):
        registry = SQLiteDecisionRegistry(tmp_db)
        result = registry.get_run("nope")
        assert result is None
        registry.close()

    def test_save_and_get_outcome(self, tmp_db, sample_result):
        registry = SQLiteDecisionRegistry(tmp_db)
        registry.save_run(sample_result)

        outcome = OutcomeRecord(
            decision_id="reg_test_001",
            selected_alternative_id="a",
            outcome_values={"actual_score": 88, "expected_score": 90},
        )
        registry.save_outcome(outcome)

        outcomes = registry.get_outcomes("reg_test_001")
        assert len(outcomes) == 1
        assert outcomes[0].selected_alternative_id == "a"
        registry.close()

    def test_count_runs(self, tmp_db, sample_result):
        registry = SQLiteDecisionRegistry(tmp_db)
        registry.save_run(sample_result)
        assert registry.count_runs() == 1
        assert registry.count_runs(domain="test_domain") == 1
        assert registry.count_runs(domain="other") == 0
        registry.close()
