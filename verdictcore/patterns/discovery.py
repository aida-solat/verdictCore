"""Pattern discovery — frequency and correlation analysis."""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import BaseModel

from verdictcore.models.intelligence import OutcomeRecord
from verdictcore.models.result import DecisionResult


class DecisionPattern(BaseModel):

    id: str
    domain: str
    pattern_type: Literal[
        "criterion_outcome_relationship",
        "evidence_reliability_issue",
        "override_pattern",
        "fragility_pattern",
        "constraint_failure_pattern",
    ]
    description: str
    confidence: float = 0.0
    support_count: int = 0
    recommendation_hint: str | None = None


class PatternReport(BaseModel):

    domain: str
    decisions_analyzed: int = 0
    patterns: list[DecisionPattern] = []


class PatternDiscovery:

    def discover(
        self,
        results: list[DecisionResult],
        outcomes: list[OutcomeRecord] | None = None,
        domain: str | None = None,
    ) -> PatternReport:
        if domain:
            results = [r for r in results if r.domain == domain]

        if not results:
            return PatternReport(domain=domain or "all")

        patterns: list[DecisionPattern] = []
        patterns.extend(self._fragility_patterns(results, domain or "all"))
        patterns.extend(self._constraint_failure_patterns(results, domain or "all"))

        return PatternReport(
            domain=domain or "all",
            decisions_analyzed=len(results),
            patterns=patterns,
        )

    @staticmethod
    def _fragility_patterns(
        results: list[DecisionResult], domain: str,
    ) -> list[DecisionPattern]:
        patterns: list[DecisionPattern] = []
        fragile_count = sum(
            1 for r in results
            if r.status.value in ("needs_review", "insufficient_data")
        )
        total = len(results)
        if total < 5:
            return patterns

        fragile_rate = fragile_count / total
        if fragile_rate >= 0.25:
            patterns.append(DecisionPattern(
                id="pat_fragility_high",
                domain=domain,
                pattern_type="fragility_pattern",
                description=(
                    f"{fragile_rate:.0%} of decisions were fragile"
                    f" (needs_review/insufficient_data)."
                ),
                confidence=min(fragile_rate + 0.2, 0.95),
                support_count=fragile_count,
                recommendation_hint=(
                    "Review evidence requirements and data completeness"
                    " policies."
                ),
            ))
        return patterns

    @staticmethod
    def _constraint_failure_patterns(
        results: list[DecisionResult], domain: str,
    ) -> list[DecisionPattern]:
        patterns: list[DecisionPattern] = []
        field_failures: Counter[str] = Counter()

        for r in results:
            for cr in r.constraint_results:
                if not cr.passed:
                    field_failures[cr.field] += 1

        total = len(results)
        for field, count in field_failures.most_common(3):
            if count >= 3 and count / total >= 0.15:
                patterns.append(DecisionPattern(
                    id=f"pat_constraint_{field}",
                    domain=domain,
                    pattern_type="constraint_failure_pattern",
                    description=(
                        f"Constraint on '{field}' failed in"
                        f" {count}/{total} decisions ({count/total:.0%})."
                    ),
                    confidence=min(count / total + 0.1, 0.90),
                    support_count=count,
                    recommendation_hint=(
                        f"Review whether '{field}' threshold is realistic"
                        f" or if alternatives need better screening."
                    ),
                ))
        return patterns
