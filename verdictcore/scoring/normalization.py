"""Min-max normalization."""

from __future__ import annotations

from typing import Literal


def normalize_values(
    values: list[float | int | None],
    direction: Literal["maximize", "minimize"],
) -> list[float | None]:
    """Scale values to [0, 1] using min-max, respecting direction."""
    numeric_values = [v for v in values if v is not None]

    if not numeric_values:
        return [None for _ in values]

    min_val = min(numeric_values)
    max_val = max(numeric_values)

    # All values identical
    if max_val == min_val:
        return [1.0 if v is not None else None for v in values]

    result: list[float | None] = []
    for v in values:
        if v is None:
            result.append(None)
        elif direction == "maximize":
            result.append((v - min_val) / (max_val - min_val))
        else:  # minimize
            result.append((max_val - v) / (max_val - min_val))

    return result
