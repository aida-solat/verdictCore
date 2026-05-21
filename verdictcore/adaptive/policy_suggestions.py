"""Adaptive policy suggestions — outcome-driven, human-approved."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from verdictcore.drift.detector import DriftReport, DriftSignal
from verdictcore.patterns.discovery import DecisionPattern, PatternReport


class PolicySuggestion(BaseModel):

    id: str
    policy_id: str | None = None
    suggestion_type: Literal[
        "adjust_weight",
        "add_constraint",
        "modify_constraint",
        "change_evidence_requirement",
        "add_review_rule",
        "change_missing_data_policy",
    ]
    target: str
    current_value: Any = None
    suggested_value: Any = None
    confidence: float = 0.0
    risk: Literal["low", "medium", "high"] = "medium"
    reason: str = ""
    supporting_patterns: list[str] = []
    requires_human_approval: bool = True


class SuggestionReport(BaseModel):

    policy_id: str | None = None
    suggestions: list[PolicySuggestion] = []
    all_require_approval: bool = True


class AdaptiveSuggester:

    def suggest(
        self,
        pattern_report: PatternReport | None = None,
        drift_report: DriftReport | None = None,
        policy_id: str | None = None,
    ) -> SuggestionReport:
        suggestions: list[PolicySuggestion] = []
        idx = 0

        if pattern_report:
            for pattern in pattern_report.patterns:
                sug = self._from_pattern(pattern, idx, policy_id)
                if sug:
                    suggestions.append(sug)
                    idx += 1

        if drift_report:
            for signal in drift_report.signals:
                sug = self._from_drift(signal, idx, policy_id)
                if sug:
                    suggestions.append(sug)
                    idx += 1

        return SuggestionReport(
            policy_id=policy_id,
            suggestions=suggestions,
            all_require_approval=True,
        )

    @staticmethod
    def _from_pattern(
        pattern: DecisionPattern, idx: int, policy_id: str | None,
    ) -> PolicySuggestion | None:
        if pattern.pattern_type == "fragility_pattern":
            return PolicySuggestion(
                id=f"sug_{idx:03d}",
                policy_id=policy_id,
                suggestion_type="add_review_rule",
                target="robustness_threshold",
                current_value="none",
                suggested_value="require_review_below_0.65",
                confidence=pattern.confidence,
                risk="low",
                reason=pattern.description,
                supporting_patterns=[pattern.id],
                requires_human_approval=True,
            )

        if pattern.pattern_type == "constraint_failure_pattern":
            return PolicySuggestion(
                id=f"sug_{idx:03d}",
                policy_id=policy_id,
                suggestion_type="modify_constraint",
                target=pattern.id.replace("pat_constraint_", ""),
                current_value="current_threshold",
                suggested_value="review_threshold",
                confidence=pattern.confidence,
                risk="medium",
                reason=pattern.description,
                supporting_patterns=[pattern.id],
                requires_human_approval=True,
            )

        return None

    @staticmethod
    def _from_drift(
        signal: DriftSignal, idx: int, policy_id: str | None,
    ) -> PolicySuggestion | None:
        if signal.drift_type == "outcome_drift":
            return PolicySuggestion(
                id=f"sug_{idx:03d}",
                policy_id=policy_id,
                suggestion_type="change_evidence_requirement",
                target="policy_evidence_requirements",
                current_value="current",
                suggested_value="strengthen",
                confidence=signal.confidence,
                risk="medium",
                reason=signal.description,
                requires_human_approval=True,
            )

        if signal.drift_type == "constraint_drift":
            return PolicySuggestion(
                id=f"sug_{idx:03d}",
                policy_id=policy_id,
                suggestion_type="modify_constraint",
                target="constraint_thresholds",
                current_value="current",
                suggested_value="review_and_adjust",
                confidence=signal.confidence,
                risk="medium",
                reason=signal.description,
                requires_human_approval=True,
            )

        return None
