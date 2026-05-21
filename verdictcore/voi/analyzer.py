"""Value-of-Information analyzer — identifies highest-impact missing data."""

from __future__ import annotations

from verdictcore.models.alternative import Alternative
from verdictcore.models.constraint import Constraint
from verdictcore.models.criterion import Criterion
from verdictcore.models.decision import DecisionInput
from verdictcore.models.evidence import Evidence
from verdictcore.models.intelligence import (
    MissingInformationItem,
    ValueOfInformationReport,
)
from verdictcore.models.result import DecisionResult, RankedAlternative


class ValueOfInformationAnalyzer:

    def analyze(
        self,
        decision_input: DecisionInput,
        decision_result: DecisionResult,
    ) -> ValueOfInformationReport:
        items: list[MissingInformationItem] = []
        evidence_map = self._build_evidence_map(decision_input.evidence)
        winner_id = decision_result.recommendation.selected_alternative_id

        for alt in decision_input.alternatives:
            for criterion in decision_input.criteria:
                val = alt.values.get(criterion.name)
                if val is not None:
                    continue

                constraint_related = self._affects_constraint(
                    criterion.name, decision_input.constraints,
                )
                near_threshold = self._is_near_threshold(
                    alt, criterion.name, decision_input.constraints,
                )
                ranking_factor = self._ranking_impact(
                    alt.id, winner_id, decision_result.rankings,
                )
                evidence_factor = self._evidence_quality_factor(
                    alt.id, criterion.name, evidence_map,
                )

                impact = self._compute_voi_score(
                    criterion_weight=criterion.weight,
                    missingness=1.0,
                    threshold_factor=1.0 if constraint_related else 0.4,
                    ranking_factor=ranking_factor,
                    evidence_factor=evidence_factor,
                )

                question = self._suggest_question(
                    alt, criterion, constraint_related,
                )
                reason = self._build_reason(
                    alt, criterion, constraint_related,
                    near_threshold, winner_id,
                )

                items.append(MissingInformationItem(
                    alternative_id=alt.id,
                    field=criterion.name,
                    criterion_weight=criterion.weight,
                    constraint_related=constraint_related,
                    near_threshold=near_threshold,
                    estimated_impact=round(min(impact, 1.0), 4),
                    reason=reason,
                    suggested_question=question,
                ))

        items.sort(key=lambda x: x.estimated_impact, reverse=True)
        return ValueOfInformationReport(
            decision_id=decision_result.decision_id,
            items=items,
        )

    @staticmethod
    def _compute_voi_score(
        criterion_weight: float,
        missingness: float,
        threshold_factor: float,
        ranking_factor: float,
        evidence_factor: float,
    ) -> float:
        return (
            criterion_weight
            * missingness
            * threshold_factor
            * ranking_factor
            * evidence_factor
        )

    @staticmethod
    def _affects_constraint(
        field: str, constraints: list[Constraint],
    ) -> bool:
        return any(c.field == field for c in constraints)

    @staticmethod
    def _is_near_threshold(
        alt: Alternative,
        field: str,
        constraints: list[Constraint],
    ) -> bool:
        val = alt.values.get(field)
        if val is None or not isinstance(val, (int, float)):
            return False
        for c in constraints:
            if c.field != field:
                continue
            if not isinstance(c.value, (int, float)):
                continue
            threshold = float(c.value)
            if threshold == 0:
                continue
            margin = abs(float(val) - threshold) / threshold
            if margin < 0.10:
                return True
        return False

    @staticmethod
    def _ranking_impact(
        alt_id: str,
        winner_id: str | None,
        rankings: list[RankedAlternative],
    ) -> float:
        if alt_id == winner_id:
            return 0.7
        for r in rankings:
            if r.alternative_id == alt_id:
                if r.blocked:
                    return 1.0
                if r.rank and r.rank <= 2:
                    return 0.7
                return 0.4
        return 0.4

    @staticmethod
    def _evidence_quality_factor(
        alt_id: str,
        field: str,
        evidence_map: dict[tuple[str, str], list[Evidence]],
    ) -> float:
        key = (alt_id, field)
        if key not in evidence_map:
            return 1.0
        qualities = []
        for ev in evidence_map[key]:
            if ev.confidence is not None:
                qualities.append(ev.confidence)
            if ev.reliability is not None:
                qualities.append(ev.reliability)
        if not qualities:
            return 1.0
        avg = sum(qualities) / len(qualities)
        if avg >= 0.8:
            return 0.1
        if avg >= 0.6:
            return 0.4
        if avg >= 0.4:
            return 0.8
        return 1.0

    @staticmethod
    def _build_evidence_map(
        evidence_list: list[Evidence],
    ) -> dict[tuple[str, str], list[Evidence]]:
        mapping: dict[tuple[str, str], list[Evidence]] = {}
        for ev in evidence_list:
            if ev.alternative_id and ev.field:
                key = (ev.alternative_id, ev.field)
                mapping.setdefault(key, []).append(ev)
        return mapping

    @staticmethod
    def _suggest_question(
        alt: Alternative,
        criterion: Criterion,
        constraint_related: bool,
    ) -> str:
        if constraint_related:
            return (
                f"Can {alt.name} provide verification for"
                f" {criterion.name}?"
            )
        return (
            f"What is {alt.name}'s value for {criterion.name}?"
        )

    @staticmethod
    def _build_reason(
        alt: Alternative,
        criterion: Criterion,
        constraint_related: bool,
        near_threshold: bool,
        winner_id: str | None,
    ) -> str:
        parts: list[str] = []
        parts.append(
            f"{alt.name} is missing data for {criterion.name}"
            f" (weight: {criterion.weight:.2f})."
        )
        if constraint_related:
            parts.append("This field is tied to a blocking constraint.")
        if near_threshold:
            parts.append("The value is near the constraint threshold.")
        if alt.id != winner_id:
            parts.append(
                "If provided, this alternative may become eligible"
                " and affect the final ranking."
            )
        return " ".join(parts)
