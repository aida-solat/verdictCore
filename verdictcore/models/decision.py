"""Top-level decision input schema."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from verdictcore.models.alternative import Alternative
from verdictcore.models.constraint import Constraint
from verdictcore.models.criterion import Criterion
from verdictcore.models.evidence import Evidence
from verdictcore.models.policy import MissingPolicy
from verdictcore.models.scenario import Scenario


class DecisionInput(BaseModel):

    decision_id: str | None = None
    question: str
    domain: str = "general"
    policy_version: str = "v1"
    missing_policy: MissingPolicy = MissingPolicy.NEEDS_REVIEW
    criteria: list[Criterion]
    constraints: list[Constraint] = []
    alternatives: list[Alternative]
    evidence: list[Evidence] = []
    scenarios: list[Scenario] = []
    metadata: dict[str, Any] = {}
