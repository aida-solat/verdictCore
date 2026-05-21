"""Constraint optimization — find optimal threshold values."""

from __future__ import annotations

from copy import deepcopy
from typing import Literal

from pydantic import BaseModel

from verdictcore.engine import Deciwa
from verdictcore.models.decision import DecisionInput


class ConstraintCandidate(BaseModel):

    value: float
    blocked_rate: float = 0.0
    average_cost: float | None = None
    risk_reduction: float | None = None
    winner: str | None = None


class ConstraintOptimizationInput(BaseModel):

    field: str
    operator: Literal[">=", "<=", ">", "<"]
    candidate_values: list[float]
    objective_metrics: list[str] = []


class ConstraintOptimizationResult(BaseModel):

    field: str
    operator: str
    candidates: list[ConstraintCandidate] = []
    recommended_threshold: float | None = None
    reason: str = ""


class ConstraintOptimizer:

    def __init__(self, engine: Deciwa | None = None) -> None:
        self._engine = engine or Deciwa(enable_sensitivity=False)

    def optimize(
        self,
        decision_input: DecisionInput,
        optimization_input: ConstraintOptimizationInput,
    ) -> ConstraintOptimizationResult:
        candidates: list[ConstraintCandidate] = []

        for val in optimization_input.candidate_values:
            perturbed = self._apply_threshold(
                decision_input, optimization_input.field,
                optimization_input.operator, val,
            )
            result = self._engine.run(perturbed)

            blocked_alts = sum(
                1 for cr in result.constraint_results
                if cr.field == optimization_input.field and not cr.passed
            )
            total_alts = len(result.rankings)
            blocked_rate = (
                blocked_alts / total_alts if total_alts > 0 else 0
            )

            winner = result.recommendation.selected_alternative_id

            candidates.append(ConstraintCandidate(
                value=val,
                blocked_rate=round(blocked_rate, 4),
                winner=winner,
            ))

        recommended, reason = self._recommend(
            candidates, optimization_input,
        )

        return ConstraintOptimizationResult(
            field=optimization_input.field,
            operator=optimization_input.operator,
            candidates=candidates,
            recommended_threshold=recommended,
            reason=reason,
        )

    @staticmethod
    def _apply_threshold(
        decision_input: DecisionInput,
        field: str,
        operator: str,
        value: float,
    ) -> DecisionInput:
        perturbed = deepcopy(decision_input)
        found = False
        for c in perturbed.constraints:
            if c.field == field and c.operator == operator:
                c.value = value
                found = True
                break
        if not found:
            from verdictcore.models.constraint import Constraint
            perturbed.constraints.append(
                Constraint(
                    field=field, operator=operator,
                    value=value, action="block",
                ),
            )
        return perturbed

    @staticmethod
    def _recommend(
        candidates: list[ConstraintCandidate],
        opt_input: ConstraintOptimizationInput,
    ) -> tuple[float | None, str]:
        if not candidates:
            return None, "No candidates evaluated."

        viable = [c for c in candidates if c.blocked_rate < 0.5]
        if not viable:
            return candidates[0].value, (
                "All thresholds block too many alternatives."
                " Using lowest threshold."
            )

        best = max(viable, key=lambda c: c.value)
        return best.value, (
            f"{opt_input.field} {opt_input.operator} {best.value}"
            f" provides meaningful filtering (blocked rate:"
            f" {best.blocked_rate:.0%}) without over-restricting."
        )
