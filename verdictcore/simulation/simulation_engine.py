"""Monte Carlo simulation engine."""

from __future__ import annotations

import random
import uuid
from collections import Counter
from copy import deepcopy

from verdictcore.engine import Deciwa
from verdictcore.models.decision import DecisionInput
from verdictcore.simulation.distributions import sample_variable
from verdictcore.simulation.simulation_result import (
    RiskMetrics,
    SimulationResult,
    WinnerDistribution,
)
from verdictcore.simulation.variables import SimulationConfig, SimulationVariable


class SimulationEngine:

    def __init__(self, base_engine: Deciwa | None = None) -> None:
        self._engine = base_engine or Deciwa(enable_sensitivity=False)

    def run(
        self,
        decision_input: DecisionInput,
        config: SimulationConfig | None = None,
        variables: list[SimulationVariable] | None = None,
        iterations: int = 5000,
        seed: int | None = 42,
    ) -> SimulationResult:
        if config is None:
            config = SimulationConfig(
                iterations=iterations,
                seed=seed,
                variables=variables or [],
            )

        rng = random.Random(config.seed)
        winners: list[str] = []
        sampled_values: dict[str, dict[str, list[float]]] = {}

        for _ in range(config.iterations):
            perturbed = self._sample_decision(decision_input, config.variables, rng)
            result = self._engine.run(perturbed)

            winner_id = result.recommendation.selected_alternative_id
            if winner_id:
                winners.append(winner_id)

            self._collect_sampled_values(perturbed, sampled_values)

        winner_dist = self._compute_winner_distribution(winners, config.iterations)
        risk_metrics = self._compute_risk_metrics(sampled_values)
        selected, reason = self._select_winner(winner_dist)
        interpretation = self._interpret(winner_dist, risk_metrics)

        return SimulationResult(
            simulation_id=f"sim_{uuid.uuid4().hex[:8]}",
            decision_id=decision_input.decision_id,
            iterations=config.iterations,
            winner_distribution=winner_dist,
            selected_alternative=selected,
            selection_reason=reason,
            risk_metrics=risk_metrics,
            interpretation=interpretation,
        )

    def _sample_decision(
        self,
        decision_input: DecisionInput,
        variables: list[SimulationVariable],
        rng: random.Random,
    ) -> DecisionInput:
        perturbed = deepcopy(decision_input)

        for var in variables:
            value = sample_variable(var, rng)

            if var.alternative_id:
                for alt in perturbed.alternatives:
                    if alt.id == var.alternative_id:
                        alt.values[var.field] = value
                        break
            else:
                for alt in perturbed.alternatives:
                    alt.values[var.field] = value

        return perturbed

    @staticmethod
    def _collect_sampled_values(
        decision: DecisionInput,
        sampled: dict[str, dict[str, list[float]]],
    ) -> None:
        for alt in decision.alternatives:
            if alt.id not in sampled:
                sampled[alt.id] = {}
            for field, value in alt.values.items():
                if isinstance(value, (int, float)):
                    sampled[alt.id].setdefault(field, []).append(float(value))

    @staticmethod
    def _compute_winner_distribution(
        winners: list[str], iterations: int,
    ) -> list[WinnerDistribution]:
        counts = Counter(winners)
        dist = [
            WinnerDistribution(
                alternative_id=alt_id,
                win_rate=round(count / max(iterations, 1), 4),
            )
            for alt_id, count in counts.most_common()
        ]
        return dist

    @staticmethod
    def _compute_risk_metrics(
        sampled: dict[str, dict[str, list[float]]],
    ) -> list[RiskMetrics]:
        metrics: list[RiskMetrics] = []

        for alt_id, fields in sampled.items():
            expected: dict[str, float] = {}
            p90: dict[str, float] = {}
            p10: dict[str, float] = {}

            for field, values in fields.items():
                if not values:
                    continue
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                expected[field] = round(sum(values) / n, 2)
                p90[field] = round(sorted_vals[int(n * 0.90)], 2)
                p10[field] = round(sorted_vals[int(n * 0.10)], 2)

            metrics.append(RiskMetrics(
                alternative_id=alt_id,
                expected_values=expected,
                p90_values=p90,
                p10_values=p10,
            ))

        return metrics

    @staticmethod
    def _select_winner(
        distribution: list[WinnerDistribution],
    ) -> tuple[str | None, str | None]:
        if not distribution:
            return None, None
        top = distribution[0]
        reason = (
            f"{top.alternative_id} won in {top.win_rate:.0%}"
            f" of simulations."
        )
        return top.alternative_id, reason

    @staticmethod
    def _interpret(
        distribution: list[WinnerDistribution],
        risk_metrics: list[RiskMetrics],
    ) -> list[str]:
        notes: list[str] = []

        if len(distribution) >= 2:
            top = distribution[0]
            second = distribution[1]
            gap = top.win_rate - second.win_rate
            if gap < 0.15:
                notes.append(
                    f"Close race: {top.alternative_id} ({top.win_rate:.0%})"
                    f" vs {second.alternative_id} ({second.win_rate:.0%})."
                    f" Decision is sensitive to uncertainty."
                )
            else:
                notes.append(
                    f"{top.alternative_id} is the robust winner"
                    f" under uncertainty ({top.win_rate:.0%})."
                )

        return notes
