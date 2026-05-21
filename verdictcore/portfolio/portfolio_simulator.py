"""Portfolio simulator — replay decisions under new policies."""

from __future__ import annotations

from copy import deepcopy

from pydantic import BaseModel

from verdictcore.engine import Deciwa
from verdictcore.models.decision import DecisionInput
from verdictcore.models.result import DecisionResult
from verdictcore.policies.model import DecisionPolicy


class PortfolioResult(BaseModel):

    decisions_analyzed: int = 0
    winner_changed_count: int = 0
    winner_changed_rate: float = 0.0
    blocked_rate_change: float = 0.0
    changed_decisions: list[str] = []
    recommendation: str = ""


class PortfolioSimulator:

    def __init__(self, engine: Deciwa | None = None) -> None:
        self._engine = engine or Deciwa(enable_sensitivity=False)

    def simulate_policy_impact(
        self,
        decisions: list[DecisionInput],
        original_results: list[DecisionResult],
        new_policy: DecisionPolicy,
    ) -> PortfolioResult:
        if not decisions or not original_results:
            return PortfolioResult(recommendation="Insufficient data.")

        result_map = {r.decision_id: r for r in original_results}
        changed_count = 0
        changed_ids: list[str] = []
        new_blocked = 0
        old_blocked = 0
        total = 0

        for decision in decisions:
            original = result_map.get(decision.decision_id)
            if original is None:
                continue

            total += 1
            modified = self._apply_policy(decision, new_policy)
            new_result = self._engine.run(modified)

            old_winner = original.recommendation.selected_alternative_id
            new_winner = new_result.recommendation.selected_alternative_id

            if old_winner != new_winner:
                changed_count += 1
                changed_ids.append(decision.decision_id)

            if original.status.value == "blocked":
                old_blocked += 1
            if new_result.status.value == "blocked":
                new_blocked += 1

        if total == 0:
            return PortfolioResult(recommendation="No matching decisions.")

        change_rate = changed_count / total
        blocked_change = (
            (new_blocked - old_blocked) / total if total > 0 else 0
        )

        recommendation = self._recommend(change_rate, blocked_change)

        return PortfolioResult(
            decisions_analyzed=total,
            winner_changed_count=changed_count,
            winner_changed_rate=round(change_rate, 4),
            blocked_rate_change=round(blocked_change, 4),
            changed_decisions=changed_ids[:50],
            recommendation=recommendation,
        )

    @staticmethod
    def _apply_policy(
        decision: DecisionInput, policy: DecisionPolicy,
    ) -> DecisionInput:
        modified = deepcopy(decision)
        modified.criteria = deepcopy(policy.criteria)
        modified.constraints = deepcopy(policy.constraints)
        return modified

    @staticmethod
    def _recommend(change_rate: float, blocked_change: float) -> str:
        if change_rate < 0.05:
            return "Policy change has minimal impact. Safe to apply."
        if change_rate < 0.20:
            return (
                "Moderate impact. Review changed decisions before applying."
            )
        if change_rate < 0.40:
            return (
                "Significant impact. Apply only to high-risk decisions"
                " initially."
            )
        return (
            "Major impact. Policy change would alter most decisions."
            " Requires careful review."
        )
