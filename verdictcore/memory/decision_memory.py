"""Decision memory — structured decision history analysis."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from verdictcore.models.intelligence import OutcomeRecord
from verdictcore.models.result import DecisionResult


class DecisionMemoryRecord(BaseModel):

    decision_id: str
    domain: str
    selected_alternative_id: str | None = None
    decision_status: str
    override_occurred: bool = False
    key_drivers: list[str] = []
    failure_modes: list[str] = []
    created_at: datetime | None = None


class MemorySummary(BaseModel):

    domain: str
    decisions_analyzed: int = 0
    most_common_winners: list[dict[str, Any]] = []
    common_failure_modes: list[str] = []
    override_rate: float = 0.0
    fragile_decision_rate: float = 0.0
    status_distribution: dict[str, int] = {}


class DecisionMemory:

    def __init__(
        self,
        results: list[DecisionResult],
        outcomes: list[OutcomeRecord] | None = None,
    ) -> None:
        self._results = results
        self._outcomes = outcomes or []
        self._records = self._build_records()

    def _build_records(self) -> list[DecisionMemoryRecord]:
        records: list[DecisionMemoryRecord] = []
        for r in self._results:
            drivers = [
                d.criterion for d in r.explanation.top_drivers[:3]
            ] if r.explanation.top_drivers else []

            records.append(DecisionMemoryRecord(
                decision_id=r.decision_id,
                domain=r.domain,
                selected_alternative_id=(
                    r.recommendation.selected_alternative_id
                ),
                decision_status=r.status.value,
                key_drivers=drivers,
                created_at=r.audit.created_at,
            ))
        return records

    def summarize(self, domain: str | None = None) -> MemorySummary:
        records = self._records
        if domain:
            records = [r for r in records if r.domain == domain]

        if not records:
            return MemorySummary(domain=domain or "all")

        winner_counts = Counter(
            r.selected_alternative_id
            for r in records
            if r.selected_alternative_id
        )
        total = len(records)
        most_common = [
            {"alternative_id": alt, "rate": round(count / total, 3)}
            for alt, count in winner_counts.most_common(5)
        ]

        status_dist = Counter(r.decision_status for r in records)
        override_count = sum(1 for r in records if r.override_occurred)
        fragile_count = sum(
            1 for r in records
            if r.decision_status in ("needs_review", "insufficient_data")
        )

        all_drivers = [d for r in records for d in r.key_drivers]
        common_drivers = [
            d for d, _ in Counter(all_drivers).most_common(5)
        ]

        return MemorySummary(
            domain=domain or "all",
            decisions_analyzed=total,
            most_common_winners=most_common,
            common_failure_modes=common_drivers,
            override_rate=round(override_count / total, 3) if total else 0,
            fragile_decision_rate=round(fragile_count / total, 3) if total else 0,
            status_distribution=dict(status_dist),
        )
