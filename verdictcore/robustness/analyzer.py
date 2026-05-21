"""Robustness analyzer — composite decision quality score."""

from __future__ import annotations

from verdictcore.models.decision import DecisionInput
from verdictcore.models.intelligence import (
    EvidenceQualityReport,
    RobustnessReport,
)
from verdictcore.models.result import DecisionResult
from verdictcore.models.scenario import ScenarioResult


class RobustnessAnalyzer:

    def analyze(
        self,
        decision_input: DecisionInput,
        decision_result: DecisionResult,
        scenario_results: list[ScenarioResult] | None = None,
        evidence_quality_report: EvidenceQualityReport | None = None,
    ) -> RobustnessReport:
        winner_id = decision_result.recommendation.selected_alternative_id

        stability = self._stability_score(decision_result)
        scenario_consistency = self._scenario_consistency(
            decision_result, scenario_results,
        )
        data_completeness = self._data_completeness(decision_input)
        evidence_quality = self._evidence_score(evidence_quality_report)
        constraint_risk = self._constraint_risk(
            decision_input, decision_result,
        )

        overall = (
            stability * 0.30
            + scenario_consistency * 0.25
            + data_completeness * 0.20
            + evidence_quality * 0.15
            + constraint_risk * 0.10
        )
        overall = round(overall, 4)
        level = _robustness_level(overall)

        risks = self._identify_risks(
            stability, scenario_consistency,
            data_completeness, evidence_quality,
            constraint_risk,
        )
        recommendations = self._build_recommendations(risks)

        return RobustnessReport(
            decision_id=decision_result.decision_id,
            selected_alternative_id=winner_id,
            stability_score=round(stability, 4),
            scenario_consistency_score=round(scenario_consistency, 4),
            data_completeness_score=round(data_completeness, 4),
            evidence_quality_score=round(evidence_quality, 4),
            constraint_risk_score=round(constraint_risk, 4),
            overall_robustness_score=overall,
            level=level,
            key_risks=risks,
            recommendations=recommendations,
        )

    @staticmethod
    def _stability_score(result: DecisionResult) -> float:
        sens = result.explanation.sensitivity
        if sens is None:
            return 0.7
        return sens.decision_stability_score

    @staticmethod
    def _scenario_consistency(
        result: DecisionResult,
        scenario_results: list[ScenarioResult] | None,
    ) -> float:
        if not scenario_results:
            return 0.8
        base_winner = result.recommendation.selected_alternative_id
        same = sum(
            1 for sr in scenario_results
            if sr.selected_alternative_id == base_winner
        )
        return round(same / len(scenario_results), 4)

    @staticmethod
    def _data_completeness(decision_input: DecisionInput) -> float:
        required_fields = {c.name for c in decision_input.criteria}
        for c in decision_input.constraints:
            required_fields.add(c.field)

        total = 0
        filled = 0
        for alt in decision_input.alternatives:
            for field in required_fields:
                total += 1
                if alt.values.get(field) is not None:
                    filled += 1

        if total == 0:
            return 1.0
        return round(filled / total, 4)

    @staticmethod
    def _evidence_score(
        report: EvidenceQualityReport | None,
    ) -> float:
        if report is None:
            return 0.5
        return report.overall_evidence_quality

    @staticmethod
    def _constraint_risk(
        decision_input: DecisionInput,
        result: DecisionResult,
    ) -> float:
        winner_id = result.recommendation.selected_alternative_id
        if not winner_id:
            return 0.5

        winner_alt = None
        for alt in decision_input.alternatives:
            if alt.id == winner_id:
                winner_alt = alt
                break
        if not winner_alt:
            return 0.5

        margins: list[float] = []
        for c in decision_input.constraints:
            val = winner_alt.values.get(c.field)
            if val is None or not isinstance(val, (int, float)):
                continue
            if not isinstance(c.value, (int, float)):
                continue
            threshold = float(c.value)
            if threshold == 0:
                continue
            margin = abs(float(val) - threshold) / threshold
            margins.append(margin)

        if not margins:
            return 0.8

        avg_margin = sum(margins) / len(margins)
        if avg_margin >= 0.20:
            return 1.0
        if avg_margin >= 0.10:
            return 0.75
        if avg_margin >= 0.05:
            return 0.45
        return 0.20

    @staticmethod
    def _identify_risks(
        stability: float,
        scenario_consistency: float,
        data_completeness: float,
        evidence_quality: float,
        constraint_risk: float,
    ) -> list[str]:
        risks: list[str] = []
        if stability < 0.6:
            risks.append(
                "Decision is sensitive to weight changes.",
            )
        if scenario_consistency < 0.6:
            risks.append(
                "Winner changes under alternative policy scenarios.",
            )
        if data_completeness < 0.8:
            risks.append(
                "Some alternatives have incomplete data.",
            )
        if evidence_quality < 0.6:
            risks.append(
                "Evidence supporting the decision is low quality.",
            )
        if constraint_risk < 0.5:
            risks.append(
                "Winner is close to constraint thresholds.",
            )
        return risks

    @staticmethod
    def _build_recommendations(risks: list[str]) -> list[str]:
        recs: list[str] = []
        for risk in risks:
            if "weight changes" in risk:
                recs.append(
                    "Review criterion weights before finalizing.",
                )
            elif "policy scenarios" in risk:
                recs.append(
                    "Run scenario analysis to understand sensitivity.",
                )
            elif "incomplete data" in risk:
                recs.append(
                    "Collect missing data before approving.",
                )
            elif "low quality" in risk:
                recs.append(
                    "Request stronger evidence for key criteria.",
                )
            elif "constraint thresholds" in risk:
                recs.append(
                    "Verify values near constraint boundaries.",
                )
        return recs


def _robustness_level(score: float) -> str:
    if score >= 0.85:
        return "strong"
    if score >= 0.65:
        return "moderate"
    if score >= 0.45:
        return "fragile"
    return "weak"
