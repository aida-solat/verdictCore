"""Decision constraints (hard/soft rules)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class Constraint(BaseModel):

    field: str
    operator: Literal[">", ">=", "<", "<=", "==", "!=", "in", "not_in"]
    value: Any
    action: Literal["block", "warn", "escalate"]
    message: str | None = None
