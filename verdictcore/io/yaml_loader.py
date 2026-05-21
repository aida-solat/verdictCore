"""YAML decision loader."""

from __future__ import annotations

from pathlib import Path

import yaml

from verdictcore.models.alternative import Alternative
from verdictcore.models.constraint import Constraint
from verdictcore.models.criterion import Criterion
from verdictcore.models.decision import DecisionInput
from verdictcore.models.evidence import Evidence
from verdictcore.models.policy import MissingPolicy
from verdictcore.models.scenario import Scenario


def load_decision_yaml(path: str | Path) -> DecisionInput:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Decision file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        raise ValueError(f"Empty or invalid YAML file: {path}")

    # Parse decision metadata
    decision_meta = data.get("decision", {})
    question = decision_meta.get("question", "")
    domain = decision_meta.get("domain", "general")
    policy_version = decision_meta.get("policy_version", "v1")
    decision_id = decision_meta.get("id")
    missing_policy_str = decision_meta.get("missing_policy", "needs_review")

    try:
        missing_policy = MissingPolicy(missing_policy_str)
    except ValueError:
        missing_policy = MissingPolicy.NEEDS_REVIEW

    # Parse criteria
    criteria_data = data.get("criteria", [])
    criteria = [Criterion(**c) for c in criteria_data]

    # Parse constraints
    constraints_data = data.get("constraints", [])
    constraints = [Constraint(**c) for c in constraints_data]

    # Parse alternatives
    alternatives_data = data.get("alternatives", [])
    alternatives = [Alternative(**a) for a in alternatives_data]

    # Parse evidence (optional)
    evidence_data = data.get("evidence", [])
    evidence = [Evidence(**e) for e in evidence_data]

    # Parse scenarios (optional, v2)
    scenarios_data = data.get("scenarios", [])
    scenarios_list = [Scenario(**s) for s in scenarios_data]

    # Parse metadata (optional)
    metadata = data.get("metadata", {})

    return DecisionInput(
        decision_id=decision_id,
        question=question,
        domain=domain,
        policy_version=policy_version,
        missing_policy=missing_policy,
        criteria=criteria,
        constraints=constraints,
        alternatives=alternatives,
        evidence=evidence,
        scenarios=scenarios_list,
        metadata=metadata,
    )
