"""Rejection explanations."""

from __future__ import annotations

from verdictcore.models.result import ConstraintResult, RankedAlternative, WhyNot


def generate_why_not(
    winner: RankedAlternative,
    rankings: list[RankedAlternative],
    constraint_results: list[ConstraintResult],
) -> list[WhyNot]:
    explanations: list[WhyNot] = []

    for ranked in rankings:
        if ranked.alternative_id == winner.alternative_id:
            continue

        reason = _build_reason(ranked, winner, constraint_results)
        explanations.append(
            WhyNot(
                alternative_id=ranked.alternative_id,
                alternative_name=ranked.name,
                reason=reason,
            )
        )

    return explanations


def _build_reason(
    alt: RankedAlternative,
    winner: RankedAlternative,
    constraint_results: list[ConstraintResult],
) -> str:
    parts: list[str] = []

    # Check if blocked
    if alt.blocked:
        failed_constraints = [
            cr for cr in constraint_results
            if cr.alternative_id == alt.alternative_id and not cr.passed and cr.action == "block"
        ]
        if failed_constraints:
            violations = [
                f"{fc.field} {fc.operator} {fc.required_value} (actual: {fc.actual_value})"
                for fc in failed_constraints
            ]
            parts.append(
                f"{alt.name} was blocked because it failed mandatory constraint(s): "
                f"{'; '.join(violations)}."
            )
        else:
            parts.append(f"{alt.name} was blocked due to constraint violations.")
        return " ".join(parts)

    # Not blocked but lower score
    gap = winner.total_score - alt.total_score
    parts.append(
        f"{alt.name} passed all constraints but scored {gap:.1f} points below "
        f"{winner.name} ({alt.total_score:.1f} vs {winner.total_score:.1f})."
    )

    # Find which criteria caused the gap
    if alt.calculation_trace and winner.calculation_trace:
        weak_criteria: list[str] = []
        for crit_name, winner_ct in winner.calculation_trace.criteria.items():
            alt_ct = alt.calculation_trace.criteria.get(crit_name)
            if alt_ct and winner_ct.weighted and alt_ct.weighted:
                if winner_ct.weighted - alt_ct.weighted > 0.02:
                    weak_criteria.append(crit_name)

        if weak_criteria:
            parts.append(
                f"It was weaker in: {', '.join(weak_criteria[:3])}."
            )

    return " ".join(parts)
