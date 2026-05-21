"""Pareto frontier analysis and dominance detection."""

from __future__ import annotations

from pydantic import BaseModel

from verdictcore.models.alternative import Alternative
from verdictcore.optimization.objectives import Objective


class ParetoAlternative(BaseModel):

    alternative_id: str
    tradeoff_profile: str | None = None
    strengths: list[str] = []
    weaknesses: list[str] = []


class DominatedAlternative(BaseModel):

    alternative_id: str
    dominated_by: list[str]
    reason: str


class ParetoReport(BaseModel):

    decision_id: str
    pareto_frontier: list[ParetoAlternative] = []
    dominated_alternatives: list[DominatedAlternative] = []
    interpretation: list[str] = []


class ParetoAnalyzer:

    def analyze(
        self,
        decision_id: str,
        alternatives: list[Alternative],
        objectives: list[Objective],
    ) -> ParetoReport:
        non_dominated: list[Alternative] = []
        dominated_map: dict[str, list[str]] = {}

        for alt in alternatives:
            dominators = self._find_dominators(alt, alternatives, objectives)
            if not dominators:
                non_dominated.append(alt)
            else:
                dominated_map[alt.id] = dominators

        frontier = [
            self._build_pareto_alt(alt, objectives, alternatives)
            for alt in non_dominated
        ]
        dominated = [
            DominatedAlternative(
                alternative_id=alt_id,
                dominated_by=doms,
                reason=self._dominance_reason(alt_id, doms, alternatives, objectives),
            )
            for alt_id, doms in dominated_map.items()
        ]
        interpretation = self._interpret(frontier, dominated)

        return ParetoReport(
            decision_id=decision_id,
            pareto_frontier=frontier,
            dominated_alternatives=dominated,
            interpretation=interpretation,
        )

    def _find_dominators(
        self,
        target: Alternative,
        all_alts: list[Alternative],
        objectives: list[Objective],
    ) -> list[str]:
        dominators: list[str] = []
        for other in all_alts:
            if other.id == target.id:
                continue
            if self._dominates(other, target, objectives):
                dominators.append(other.id)
        return dominators

    @staticmethod
    def _dominates(
        a: Alternative, b: Alternative, objectives: list[Objective],
    ) -> bool:
        at_least_as_good = True
        strictly_better_in_one = False

        for obj in objectives:
            a_val = a.values.get(obj.field)
            b_val = b.values.get(obj.field)

            if a_val is None or b_val is None:
                at_least_as_good = False
                break

            a_f = float(a_val)
            b_f = float(b_val)

            if obj.direction == "maximize":
                if a_f < b_f:
                    at_least_as_good = False
                    break
                if a_f > b_f:
                    strictly_better_in_one = True
            else:
                if a_f > b_f:
                    at_least_as_good = False
                    break
                if a_f < b_f:
                    strictly_better_in_one = True

        return at_least_as_good and strictly_better_in_one

    @staticmethod
    def _build_pareto_alt(
        alt: Alternative,
        objectives: list[Objective],
        all_alts: list[Alternative],
    ) -> ParetoAlternative:
        strengths: list[str] = []
        weaknesses: list[str] = []

        for obj in objectives:
            val = alt.values.get(obj.field)
            if val is None:
                continue
            vals = [
                float(a.values.get(obj.field, 0))
                for a in all_alts if a.values.get(obj.field) is not None
            ]
            if not vals:
                continue
            rank = (
                sorted(vals, reverse=(obj.direction == "maximize")).index(float(val))
            )
            if rank == 0:
                strengths.append(obj.field)
            elif rank >= len(vals) - 1:
                weaknesses.append(obj.field)

        return ParetoAlternative(
            alternative_id=alt.id,
            strengths=strengths,
            weaknesses=weaknesses,
        )

    @staticmethod
    def _dominance_reason(
        alt_id: str,
        dominators: list[str],
        alternatives: list[Alternative],
        objectives: list[Objective],
    ) -> str:
        dom_names = ", ".join(dominators[:3])
        return f"{alt_id} is dominated by {dom_names} across all objectives."

    @staticmethod
    def _interpret(
        frontier: list[ParetoAlternative],
        dominated: list[DominatedAlternative],
    ) -> list[str]:
        notes: list[str] = []
        if len(frontier) == 1:
            notes.append(
                f"{frontier[0].alternative_id} dominates all others."
                f" Clear winner."
            )
        elif len(frontier) > 1:
            ids = ", ".join(p.alternative_id for p in frontier)
            notes.append(
                f"Pareto frontier contains {len(frontier)} alternatives:"
                f" {ids}. Trade-offs exist."
            )
        if dominated:
            notes.append(
                f"{len(dominated)} alternative(s) are dominated and"
                f" can be safely eliminated."
            )
        return notes
