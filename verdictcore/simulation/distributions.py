"""Distribution sampling for simulation variables."""

from __future__ import annotations

import random

from verdictcore.simulation.variables import SimulationVariable


def sample_variable(var: SimulationVariable, rng: random.Random) -> float | str:
    dist = var.distribution
    params = var.parameters

    if dist == "fixed":
        return float(params["value"])

    if dist == "normal":
        value = rng.gauss(float(params["mean"]), float(params["std"]))
        return _apply_bounds(value, var.bounds)

    if dist == "triangular":
        value = rng.triangular(
            float(params["min"]),
            float(params["max"]),
            float(params["mode"]),
        )
        return _apply_bounds(value, var.bounds)

    if dist == "uniform":
        value = rng.uniform(float(params["min"]), float(params["max"]))
        return _apply_bounds(value, var.bounds)

    if dist == "beta":
        value = rng.betavariate(
            float(params["alpha"]),
            float(params["beta"]),
        )
        return _apply_bounds(value, var.bounds)

    if dist == "categorical":
        values = params.get("values", {})
        if isinstance(values, dict):
            items = list(values.keys())
            weights = [float(v) for v in values.values()]
            return rng.choices(items, weights=weights, k=1)[0]
        return str(rng.choice(values))

    raise ValueError(f"Unsupported distribution: {dist}")


def _apply_bounds(
    value: float, bounds: dict[str, float] | None,
) -> float:
    if bounds is None:
        return value
    if "min" in bounds:
        value = max(value, bounds["min"])
    if "max" in bounds:
        value = min(value, bounds["max"])
    return value
