"""Scenario engine — run decisions under alternative assumptions."""

from __future__ import annotations

from typing import Any

from verdictcore.engine import Deciwa
from verdictcore.models.decision import DecisionInput
from verdictcore.models.result import DecisionResult
from verdictcore.models.scenario import Scenario, ScenarioResult


class ScenarioEngine:

    def __init__(self, engine: Deciwa | None = None) -> None:
        self._engine = engine or Deciwa(enable_sensitivity=False)

    def run(
        self,
        base_decision: DecisionInput,
        scenarios: list[Scenario],
    ) -> list[ScenarioResult]:
        base_result = self._engine.run(base_decision)
        base_winner = (
            base_result.recommendation.selected_alternative_id
        )

        results: list[ScenarioResult] = []
        for scenario in scenarios:
            modified = self._apply_scenario(base_decision, scenario)
            scenario_result = self._engine.run(modified)
            winner_id = scenario_result.recommendation.selected_alternative_id
            winner_name = scenario_result.recommendation.selected_alternative_name

            delta = self._compute_policy_delta(
                base_decision, scenario,
            )
            explanation = self._build_explanation(
                scenario, base_winner, winner_id, winner_name,
            )

            results.append(ScenarioResult(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                status=scenario_result.status,
                selected_alternative_id=winner_id,
                selected_alternative_name=winner_name,
                rankings=scenario_result.rankings,
                changed_from_base=winner_id != base_winner,
                explanation=explanation,
                policy_delta=delta,
            ))

        return results

    def consistency_score(
        self,
        base_result: DecisionResult,
        scenario_results: list[ScenarioResult],
    ) -> float:
        if not scenario_results:
            return 1.0
        base_winner = base_result.recommendation.selected_alternative_id
        same = sum(
            1 for sr in scenario_results
            if sr.selected_alternative_id == base_winner
        )
        return round(same / len(scenario_results), 4)

    def _apply_scenario(
        self,
        base: DecisionInput,
        scenario: Scenario,
    ) -> DecisionInput:
        criteria = []
        overrides = scenario.criteria_overrides
        for c in base.criteria:
            if c.name in overrides:
                criteria.append(c.model_copy(
                    update={"weight": overrides[c.name]},
                ))
            else:
                criteria.append(c)

        alternatives = []
        for alt in base.alternatives:
            if alt.id in scenario.value_overrides:
                merged = {**alt.values, **scenario.value_overrides[alt.id]}
                alternatives.append(alt.model_copy(
                    update={"values": merged},
                ))
            else:
                alternatives.append(alt)

        constraints = (
            scenario.constraint_overrides
            if scenario.constraint_overrides
            else base.constraints
        )

        return base.model_copy(update={
            "criteria": criteria,
            "constraints": constraints,
            "alternatives": alternatives,
        })

    @staticmethod
    def _compute_policy_delta(
        base: DecisionInput,
        scenario: Scenario,
    ) -> dict[str, Any]:
        delta: dict[str, Any] = {}
        base_weights = {c.name: c.weight for c in base.criteria}
        for name, new_weight in scenario.criteria_overrides.items():
            base_weight = base_weights.get(name)
            if base_weight is not None and base_weight != new_weight:
                delta[name] = {"base": base_weight, "scenario": new_weight}
        return delta

    @staticmethod
    def _build_explanation(
        scenario: Scenario,
        base_winner: str | None,
        scenario_winner: str | None,
        scenario_winner_name: str | None,
    ) -> str:
        if scenario_winner == base_winner:
            return (
                f"Winner unchanged under '{scenario.name}' scenario."
            )

        changed_weights = []
        for name, val in scenario.criteria_overrides.items():
            changed_weights.append(f"{name}={val:.2f}")

        weight_desc = ", ".join(changed_weights) if changed_weights else ""
        winner_label = scenario_winner_name or scenario_winner or "none"

        if weight_desc:
            return (
                f"{winner_label} becomes the winner when"
                f" weights change to [{weight_desc}]."
            )
        return f"{winner_label} becomes the winner under '{scenario.name}'."
