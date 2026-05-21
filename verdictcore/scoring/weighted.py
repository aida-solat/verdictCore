"""Weighted scoring with min-max normalization."""

from __future__ import annotations

from verdictcore.models.alternative import Alternative
from verdictcore.models.criterion import Criterion
from verdictcore.models.policy import MissingPolicy
from verdictcore.models.result import CalculationTrace, CriterionTrace
from verdictcore.scoring.normalization import normalize_values


class WeightedScorer:

    def __init__(
        self,
        criteria: list[Criterion],
        alternatives: list[Alternative],
        missing_policy: MissingPolicy = MissingPolicy.NEEDS_REVIEW,
    ) -> None:
        self.criteria = criteria
        self.alternatives = alternatives
        self.missing_policy = missing_policy
        self._has_missing_data = False

    @property
    def has_missing_data(self) -> bool:
        return self._has_missing_data

    def score(self) -> list[CalculationTrace]:
        traces: list[CalculationTrace] = []

        # Pre-compute normalized values per criterion
        normalized_per_criterion: dict[str, list[float | None]] = {}

        for criterion in self.criteria:
            raw_values: list[float | int | None] = []
            for alt in self.alternatives:
                val = alt.values.get(criterion.name)
                if isinstance(val, (int, float)):
                    raw_values.append(val)
                else:
                    raw_values.append(None)
                    self._has_missing_data = True

            normalized_per_criterion[criterion.name] = normalize_values(
                raw_values, criterion.direction
            )

        # Build traces
        for i, alt in enumerate(self.alternatives):
            criteria_traces: dict[str, CriterionTrace] = {}
            total_score = 0.0
            total_weight_used = 0.0

            for criterion in self.criteria:
                raw_val = alt.values.get(criterion.name)
                normalized = normalized_per_criterion[criterion.name][i]

                if normalized is not None:
                    weighted = normalized * criterion.weight
                    total_score += weighted
                    total_weight_used += criterion.weight
                else:
                    weighted = None
                    if self.missing_policy == MissingPolicy.PENALIZE:
                        # Penalize: count as 0
                        total_weight_used += criterion.weight

                raw_numeric = raw_val if isinstance(raw_val, (int, float)) else None
                criteria_traces[criterion.name] = CriterionTrace(
                    raw=raw_numeric,
                    normalized=normalized,
                    weight=criterion.weight,
                    weighted=weighted,
                )

            # Normalize total score if ignoring missing (adjust to used weight)
            if self.missing_policy == MissingPolicy.IGNORE and total_weight_used > 0:
                total_score = total_score / total_weight_used

            # Scale to 0-100 for readability
            final_score = round(total_score * 100, 2)

            traces.append(
                CalculationTrace(
                    alternative_id=alt.id,
                    alternative_name=alt.name,
                    criteria=criteria_traces,
                    total_score=final_score,
                )
            )

        return traces
