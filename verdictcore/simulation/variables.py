"""Simulation variable model."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class SimulationVariable(BaseModel):

    field: str
    alternative_id: str | None = None
    distribution: Literal[
        "fixed",
        "normal",
        "triangular",
        "uniform",
        "beta",
        "categorical",
    ]
    parameters: dict[str, Any]
    bounds: dict[str, float] | None = None
    description: str | None = None


class SimulationConfig(BaseModel):

    iterations: int = 5000
    seed: int | None = 42
    variables: list[SimulationVariable] = []
