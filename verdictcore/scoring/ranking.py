"""Alternative ranking by score."""

from __future__ import annotations

from verdictcore.models.result import CalculationTrace, RankedAlternative


def rank_alternatives(
    traces: list[CalculationTrace],
    blocked_ids: set[str],
    warnings_map: dict[str, list[str]],
) -> list[RankedAlternative]:
    ranked: list[RankedAlternative] = []

    # Sort non-blocked by score descending
    eligible = [(t, False) for t in traces if t.alternative_id not in blocked_ids]
    blocked = [(t, True) for t in traces if t.alternative_id in blocked_ids]

    eligible.sort(key=lambda x: x[0].total_score, reverse=True)

    for rank_num, (trace, is_blocked) in enumerate(eligible, start=1):
        ranked.append(
            RankedAlternative(
                alternative_id=trace.alternative_id,
                name=trace.alternative_name,
                rank=rank_num,
                total_score=trace.total_score,
                blocked=False,
                warnings=warnings_map.get(trace.alternative_id, []),
                calculation_trace=trace,
            )
        )

    for trace, _ in blocked:
        ranked.append(
            RankedAlternative(
                alternative_id=trace.alternative_id,
                name=trace.alternative_name,
                rank=None,
                total_score=trace.total_score,
                blocked=True,
                warnings=warnings_map.get(trace.alternative_id, []),
                calculation_trace=trace,
            )
        )

    return ranked
