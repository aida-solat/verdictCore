"""Objective model for multi-objective optimization."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Objective(BaseModel):

    field: str
    direction: Literal["minimize", "maximize"]
    priority: Literal["low", "medium", "high"] | None = None
