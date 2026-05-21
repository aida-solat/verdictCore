"""Constraint evaluator."""

from __future__ import annotations

from typing import Any

from verdictcore.models.alternative import Alternative
from verdictcore.models.constraint import Constraint
from verdictcore.models.result import ConstraintResult


class ConstraintEvaluator:

    def __init__(
        self,
        constraints: list[Constraint],
        alternatives: list[Alternative],
    ) -> None:
        self.constraints = constraints
        self.alternatives = alternatives

    def evaluate(self) -> list[ConstraintResult]:
        results: list[ConstraintResult] = []

        for alt in self.alternatives:
            for constraint in self.constraints:
                actual_value = alt.values.get(constraint.field)
                passed = self._check(actual_value, constraint.operator, constraint.value)

                results.append(
                    ConstraintResult(
                        alternative_id=alt.id,
                        alternative_name=alt.name,
                        field=constraint.field,
                        operator=constraint.operator,
                        required_value=constraint.value,
                        actual_value=actual_value,
                        action=constraint.action,
                        passed=passed,
                        message=constraint.message if not passed else None,
                    )
                )

        return results

    def get_blocked_ids(self, results: list[ConstraintResult]) -> set[str]:
        blocked: set[str] = set()
        for r in results:
            if not r.passed and r.action == "block":
                blocked.add(r.alternative_id)
        return blocked

    def get_warnings_map(self, results: list[ConstraintResult]) -> dict[str, list[str]]:
        warnings: dict[str, list[str]] = {}
        for r in results:
            if not r.passed and r.action == "warn":
                msg = r.message or (
                    f"{r.field} {r.operator} {r.required_value}"
                    f" not met (actual: {r.actual_value})"
                )
                warnings.setdefault(r.alternative_id, []).append(msg)
        return warnings

    def get_escalation_ids(self, results: list[ConstraintResult]) -> set[str]:
        escalated: set[str] = set()
        for r in results:
            if not r.passed and r.action == "escalate":
                escalated.add(r.alternative_id)
        return escalated

    @staticmethod
    def _check(actual: Any, operator: str, required: Any) -> bool:
        if actual is None:
            return False

        try:
            if operator == ">":
                return float(actual) > float(required)
            elif operator == ">=":
                return float(actual) >= float(required)
            elif operator == "<":
                return float(actual) < float(required)
            elif operator == "<=":
                return float(actual) <= float(required)
            elif operator == "==":
                return bool(actual == required)
            elif operator == "!=":
                return bool(actual != required)
            elif operator == "in":
                return actual in required
            elif operator == "not_in":
                return actual not in required
            else:
                return False
        except (TypeError, ValueError):
            return False
