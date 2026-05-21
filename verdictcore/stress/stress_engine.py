"""Stress testing engine — apply perturbations and re-run decisions."""

from __future__ import annotations

from copy import deepcopy
from typing import Literal

from pydantic import BaseModel

from verdictcore.engine import Deciwa
from verdictcore.models.decision import DecisionInput
from verdictcore.stress.stress_scenario import Perturbation, StressScenario


class StressResult(BaseModel):

    scenario_id: str
    scenario_name: str
    winner: str | None = None
    base_winner: str | None = None
    winner_changed: bool = False
    risk_level: Literal["low", "medium", "high"] = "low"
    interpretation: str = ""


class StressTestReport(BaseModel):

    decision_id: str
    base_winner: str | None = None
    stress_results: list[StressResult] = []
    overall_vulnerability: Literal["low", "medium", "high"] = "low"


class StressTestEngine:

    def __init__(self, base_engine: Deciwa | None = None) -> None:
        self._engine = base_engine or Deciwa(enable_sensitivity=False)

    def run(
        self,
        decision_input: DecisionInput,
        stress_scenarios: list[StressScenario],
    ) -> StressTestReport:
        base_result = self._engine.run(decision_input)
        base_winner = base_result.recommendation.selected_alternative_id

        stress_results: list[StressResult] = []

        for scenario in stress_scenarios:
            perturbed = self._apply_perturbations(
                decision_input, scenario.perturbations,
            )
            stressed_result = self._engine.run(perturbed)
            stressed_winner = (
                stressed_result.recommendation.selected_alternative_id
            )

            changed = stressed_winner != base_winner
            risk = "high" if changed else "low"
            interpretation = self._interpret(
                scenario, base_winner, stressed_winner, changed,
            )

            stress_results.append(StressResult(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                winner=stressed_winner,
                base_winner=base_winner,
                winner_changed=changed,
                risk_level=risk,
                interpretation=interpretation,
            ))

        vulnerability = self._assess_vulnerability(stress_results)

        return StressTestReport(
            decision_id=decision_input.decision_id,
            base_winner=base_winner,
            stress_results=stress_results,
            overall_vulnerability=vulnerability,
        )

    def _apply_perturbations(
        self,
        decision_input: DecisionInput,
        perturbations: list[Perturbation],
    ) -> DecisionInput:
        perturbed = deepcopy(decision_input)

        for p in perturbations:
            if p.target in ("alternative_value", "all_values"):
                self._perturb_values(perturbed, p)
            elif p.target == "constraint":
                self._perturb_constraint(perturbed, p)
            elif p.target == "criterion":
                self._perturb_criterion(perturbed, p)

        return perturbed

    @staticmethod
    def _perturb_values(
        decision: DecisionInput, p: Perturbation,
    ) -> None:
        for alt in decision.alternatives:
            if p.alternative_id and alt.id != p.alternative_id:
                continue
            if p.field in alt.values:
                current = alt.values[p.field]
                if isinstance(current, (int, float)):
                    alt.values[p.field] = _apply_op(
                        float(current), p.operation, float(p.value),
                    )

    @staticmethod
    def _perturb_constraint(
        decision: DecisionInput, p: Perturbation,
    ) -> None:
        for c in decision.constraints:
            if c.field == p.field:
                if isinstance(c.value, (int, float)):
                    c.value = _apply_op(
                        float(c.value), p.operation, float(p.value),
                    )

    @staticmethod
    def _perturb_criterion(
        decision: DecisionInput, p: Perturbation,
    ) -> None:
        for c in decision.criteria:
            if c.name == p.field:
                c.weight = _apply_op(
                    c.weight, p.operation, float(p.value),
                )

    @staticmethod
    def _interpret(
        scenario: StressScenario,
        base_winner: str | None,
        stressed_winner: str | None,
        changed: bool,
    ) -> str:
        if changed:
            return (
                f"Under '{scenario.name}', winner changed from"
                f" {base_winner} to {stressed_winner}."
                f" Decision is vulnerable to this stress."
            )
        return (
            f"Under '{scenario.name}', {base_winner} remains"
            f" the winner. Decision is resilient."
        )

    @staticmethod
    def _assess_vulnerability(
        results: list[StressResult],
    ) -> Literal["low", "medium", "high"]:
        if not results:
            return "low"
        changed_count = sum(1 for r in results if r.winner_changed)
        rate = changed_count / len(results)
        if rate >= 0.5:
            return "high"
        if rate >= 0.25:
            return "medium"
        return "low"


def _apply_op(current: float, operation: str, value: float) -> float:
    if operation == "multiply":
        return current * value
    if operation == "add":
        return current + value
    if operation == "subtract":
        return current - value
    if operation == "set":
        return value
    return current
