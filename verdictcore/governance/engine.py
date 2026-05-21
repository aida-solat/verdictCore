"""Governance engine — evaluate rules, assign risk, produce governance report."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from verdictcore.models.intelligence import RobustnessReport
from verdictcore.models.result import DecisionResult


class GovernanceRule(BaseModel):

    id: str
    name: str
    condition: str
    action: Literal[
        "require_review",
        "require_approval",
        "block",
        "escalate",
        "add_warning",
    ]
    message: str


class GovernanceAction(BaseModel):

    action: str
    rule_id: str
    message: str


class GovernanceReport(BaseModel):

    decision_id: str
    risk_level: Literal["low", "medium", "high", "critical"]
    review_required: bool = False
    approval_required: bool = False
    blocked: bool = False
    reasons: list[str] = []
    actions: list[GovernanceAction] = []


class GovernanceEngine:

    def __init__(self, rules: list[GovernanceRule] | None = None) -> None:
        self._rules = rules or []

    @classmethod
    def from_rules(cls, rules: list[dict[str, Any]]) -> GovernanceEngine:
        parsed = [GovernanceRule(**r) for r in rules]
        return cls(rules=parsed)

    def evaluate(
        self,
        decision_result: DecisionResult,
        robustness: RobustnessReport | None = None,
        context: dict[str, Any] | None = None,
    ) -> GovernanceReport:
        ctx = self._build_context(decision_result, robustness, context)
        actions: list[GovernanceAction] = []
        reasons: list[str] = []

        for rule in self._rules:
            if self._evaluate_condition(rule.condition, ctx):
                actions.append(GovernanceAction(
                    action=rule.action,
                    rule_id=rule.id,
                    message=rule.message,
                ))
                reasons.append(rule.message)

        risk_level = self._assess_risk(decision_result, robustness, ctx)
        review_required = any(
            a.action in ("require_review", "require_approval", "escalate")
            for a in actions
        )
        approval_required = any(
            a.action == "require_approval" for a in actions
        )
        blocked = any(a.action == "block" for a in actions)

        return GovernanceReport(
            decision_id=decision_result.decision_id,
            risk_level=risk_level,
            review_required=review_required,
            approval_required=approval_required,
            blocked=blocked,
            reasons=reasons,
            actions=actions,
        )

    @staticmethod
    def _build_context(
        result: DecisionResult,
        robustness: RobustnessReport | None,
        extra: dict[str, Any] | None,
    ) -> dict[str, Any]:
        ctx: dict[str, Any] = {
            "status": result.status.value,
            "decision_id": result.decision_id,
            "domain": result.domain,
            "metadata": result.metadata,
        }
        if robustness:
            ctx["robustness"] = {
                "level": robustness.level,
                "score": robustness.overall_robustness_score,
            }
        if extra:
            ctx.update(extra)
        return ctx

    @staticmethod
    def _evaluate_condition(condition: str, ctx: dict[str, Any]) -> bool:
        try:
            return bool(eval(condition, {"__builtins__": {}}, ctx))  # noqa: S307
        except Exception:
            return False

    @staticmethod
    def _assess_risk(
        result: DecisionResult,
        robustness: RobustnessReport | None,
        ctx: dict[str, Any],
    ) -> Literal["low", "medium", "high", "critical"]:
        score = 0

        if robustness:
            if robustness.level == "weak":
                score += 3
            elif robustness.level == "fragile":
                score += 2
            elif robustness.level == "moderate":
                score += 1

        spend = ctx.get("metadata", {}).get("spend", 0)
        if isinstance(spend, (int, float)):
            if spend >= 1_000_000:
                score += 3
            elif spend >= 500_000:
                score += 2
            elif spend >= 100_000:
                score += 1

        if result.status.value in ("needs_review", "insufficient_data"):
            score += 2

        if score >= 5:
            return "critical"
        if score >= 3:
            return "high"
        if score >= 2:
            return "medium"
        return "low"
