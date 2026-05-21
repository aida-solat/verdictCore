"""Tests for YAML loading."""

import tempfile
from pathlib import Path

import pytest

from verdictcore.io.yaml_loader import load_decision_yaml

VALID_YAML = """
decision:
  id: test_001
  domain: test_domain
  question: Which option is best?
  policy_version: v1

criteria:
  - name: quality
    weight: 0.6
    direction: maximize
  - name: cost
    weight: 0.4
    direction: minimize

constraints:
  - field: quality
    operator: ">="
    value: 50
    action: block

alternatives:
  - id: opt_a
    name: Option A
    values:
      quality: 80
      cost: 100
  - id: opt_b
    name: Option B
    values:
      quality: 60
      cost: 50
"""


class TestYamlLoader:
    def test_load_valid_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(VALID_YAML)
            f.flush()
            decision = load_decision_yaml(f.name)

        assert decision.decision_id == "test_001"
        assert decision.question == "Which option is best?"
        assert decision.domain == "test_domain"
        assert len(decision.criteria) == 2
        assert len(decision.constraints) == 1
        assert len(decision.alternatives) == 2

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_decision_yaml("/nonexistent/path/decision.yaml")

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            with pytest.raises(ValueError):
                load_decision_yaml(f.name)

    def test_load_example_file(self):
        """Load the actual example file."""
        example_path = (
            Path(__file__).parent.parent
            / "examples" / "ai_model_selection" / "decision.yaml"
        )
        if example_path.exists():
            decision = load_decision_yaml(example_path)
            assert decision.decision_id == "ai_model_healthcare_rag_001"
            assert len(decision.alternatives) == 3
            assert len(decision.criteria) == 5
            assert len(decision.constraints) == 2
