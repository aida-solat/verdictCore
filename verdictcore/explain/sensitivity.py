"""Weight sensitivity analysis."""

from __future__ import annotations

from typing import Any

from verdictcore.models.alternative import Alternative
from verdictcore.models.criterion import Criterion
from verdictcore.models.policy import MissingPolicy
from verdictcore.models.result import SensitivityResult
from verdictcore.scoring.weighted import WeightedScorer


def run_sensitivity_analysis(
    criteria: list[Criterion],
    alternatives: list[Alternative],
    blocked_ids: set[str],
    winner_id: str,
    missing_policy: MissingPolicy = MissingPolicy.NEEDS_REVIEW,
    steps: int = 20,
) -> SensitivityResult:
    total_tests = 0
    flip_count = 0
    sensitive_to: list[str] = []
    winner_changes_if: list[dict[str, Any]] = []

    eligible_alts = [a for a in alternatives if a.id not in blocked_ids]
    if len(eligible_alts) < 2:
        return SensitivityResult(
            decision_stability_score=1.0,
            level="stable",
            sensitive_to=[],
            winner_changes_if=[],
        )

    for target_criterion in criteria:
        flipped_at: float | None = None
        new_winner_name: str | None = None

        for step in range(1, steps + 1):
            test_weight = step * (0.80 / steps)
            total_tests += 1

            # Redistribute remaining weight proportionally
            modified_criteria = _redistribute_weights(criteria, target_criterion.name, test_weight)

            scorer = WeightedScorer(modified_criteria, eligible_alts, missing_policy)
            traces = scorer.score()

            # Find new winner
            best = max(traces, key=lambda t: t.total_score)
            if best.alternative_id != winner_id:
                flip_count += 1
                if flipped_at is None:
                    flipped_at = round(test_weight, 3)
                    new_winner_name = best.alternative_name

        if flipped_at is not None:
            sensitive_to.append(target_criterion.name)
            winner_changes_if.append({
                "criterion": target_criterion.name,
                "threshold": flipped_at,
                "new_winner": new_winner_name,
            })

    # Compute stability score
    if total_tests == 0:
        stability_score = 1.0
    else:
        stability_score = round(1.0 - (flip_count / total_tests), 2)

    # Determine level
    if stability_score >= 0.85:
        level = "stable"
    elif stability_score >= 0.65:
        level = "moderately_stable"
    elif stability_score >= 0.40:
        level = "fragile"
    else:
        level = "unstable"

    return SensitivityResult(
        decision_stability_score=stability_score,
        level=level,
        sensitive_to=sensitive_to,
        winner_changes_if=winner_changes_if,
    )


def _redistribute_weights(
    criteria: list[Criterion],
    target_name: str,
    target_weight: float,
) -> list[Criterion]:
    other_criteria = [c for c in criteria if c.name != target_name]
    original_other_sum = sum(c.weight for c in other_criteria)

    remaining = 1.0 - target_weight
    modified: list[Criterion] = []

    for c in criteria:
        if c.name == target_name:
            modified.append(c.model_copy(update={"weight": target_weight}))
        else:
            if original_other_sum > 0:
                new_weight = (c.weight / original_other_sum) * remaining
            else:
                new_weight = remaining / len(other_criteria) if other_criteria else 0
            modified.append(c.model_copy(update={"weight": new_weight}))

    return modified
