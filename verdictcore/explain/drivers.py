"""Top driver computation."""

from __future__ import annotations

from verdictcore.models.result import CalculationTrace, TopDriver


def compute_top_drivers(
    winner_trace: CalculationTrace,
    max_drivers: int = 5,
) -> list[TopDriver]:
    if winner_trace.total_score == 0:
        return []

    impacts: list[tuple[str, float]] = []
    for name, ct in winner_trace.criteria.items():
        if ct.weighted is not None:
            # Impact as proportion of total weighted score (scaled to 100)
            impact = round(ct.weighted / (winner_trace.total_score / 100), 2)
            impacts.append((name, impact))

    impacts.sort(key=lambda x: x[1], reverse=True)

    return [
        TopDriver(criterion=name, impact=impact)
        for name, impact in impacts[:max_drivers]
    ]
