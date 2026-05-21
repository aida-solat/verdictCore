"""Winner selection explanation."""

from __future__ import annotations

from verdictcore.models.result import ConstraintResult, RankedAlternative


def generate_why_selected(
    winner: RankedAlternative,
    rankings: list[RankedAlternative],
    constraint_results: list[ConstraintResult],
) -> str:
    parts: list[str] = []

    # Check if all constraints passed
    winner_constraints = [
        cr for cr in constraint_results
        if cr.alternative_id == winner.alternative_id
    ]
    all_passed = all(cr.passed for cr in winner_constraints)

    if all_passed and winner_constraints:
        parts.append(
            f"{winner.name} was selected because it passed all mandatory constraints "
            f"and achieved the highest weighted score ({winner.total_score:.1f})."
        )
    elif not winner_constraints:
        parts.append(
            f"{winner.name} was selected because it achieved the highest weighted score "
            f"({winner.total_score:.1f})."
        )
    else:
        parts.append(
            f"{winner.name} was selected with the highest"
            f" weighted score ({winner.total_score:.1f})."
        )

    # How many alternatives were blocked?
    blocked_count = sum(1 for r in rankings if r.blocked)
    if blocked_count > 0:
        blocked_names = [r.name for r in rankings if r.blocked]
        parts.append(
            f"{blocked_count} alternative(s) were blocked due to constraint violations: "
            f"{', '.join(blocked_names)}."
        )

    # Runner-up info
    runners = [r for r in rankings if not r.blocked and r.alternative_id != winner.alternative_id]
    if runners:
        runner = runners[0]
        gap = winner.total_score - runner.total_score
        parts.append(
            f"The next best option was {runner.name} with a score of {runner.total_score:.1f} "
            f"(gap: {gap:.1f} points)."
        )

    return " ".join(parts)
