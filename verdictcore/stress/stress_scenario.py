"""Stress scenario and perturbation models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Perturbation(BaseModel):

    target: Literal[
        "criterion",
        "constraint",
        "alternative_value",
        "all_values",
    ]
    field: str
    alternative_id: str | None = None
    operation: Literal["multiply", "add", "subtract", "set"]
    value: float | int | str


class StressScenario(BaseModel):

    id: str
    name: str
    description: str | None = None
    perturbations: list[Perturbation]
