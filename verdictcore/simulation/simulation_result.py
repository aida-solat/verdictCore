"""Simulation result models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class WinnerDistribution(BaseModel):

    alternative_id: str
    win_rate: float


class RiskMetrics(BaseModel):

    alternative_id: str
    expected_values: dict[str, float] = {}
    p90_values: dict[str, float] = {}
    p10_values: dict[str, float] = {}
    overrun_probabilities: dict[str, float] = {}


class SimulationResult(BaseModel):

    simulation_id: str
    decision_id: str
    iterations: int
    winner_distribution: list[WinnerDistribution] = []
    selected_alternative: str | None = None
    selection_reason: str | None = None
    risk_metrics: list[RiskMetrics] = []
    interpretation: list[str] = []
    metadata: dict[str, Any] = {}
