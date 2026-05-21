"""Scenario models for what-if analysis."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from verdictcore.models.constraint import Constraint
from verdictcore.models.result import (
    DecisionStatus,
    RankedAlternative,
)


class Scenario(BaseModel):

    id: str
    name: str
    description: str | None = None
    criteria_overrides: dict[str, float] = {}
    constraint_overrides: list[Constraint] = []
    value_overrides: dict[str, dict[str, float | int | str | None]] = {}
    metadata: dict[str, Any] = {}


class ScenarioResult(BaseModel):

    scenario_id: str
    scenario_name: str
    status: DecisionStatus
    selected_alternative_id: str | None
    selected_alternative_name: str | None = None
    rankings: list[RankedAlternative]
    changed_from_base: bool
    explanation: str
    policy_delta: dict[str, Any] = {}
