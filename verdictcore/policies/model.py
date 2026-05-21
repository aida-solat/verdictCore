"""Policy model for versioned decision governance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from verdictcore.models.constraint import Constraint
from verdictcore.models.criterion import Criterion


class DecisionPolicy(BaseModel):

    policy_id: str
    version: str
    domain: str
    description: str | None = None
    criteria: list[Criterion]
    constraints: list[Constraint] = []
    missing_data_policy: Literal["penalize", "ignore", "needs_review"] = "needs_review"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    created_by: str | None = None
    metadata: dict[str, Any] = {}

    @property
    def criteria_map(self) -> dict[str, Criterion]:
        return {c.name: c for c in self.criteria}

    @property
    def weight_map(self) -> dict[str, float]:
        return {c.name: c.weight for c in self.criteria}
