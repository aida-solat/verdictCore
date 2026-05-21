"""Abstract registry protocol."""

from __future__ import annotations

from typing import Protocol

from verdictcore.models.intelligence import OutcomeRecord
from verdictcore.models.result import DecisionResult


class DecisionQuery:

    def __init__(
        self,
        domain: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> None:
        self.domain = domain
        self.status = status
        self.limit = limit


class DecisionRegistry(Protocol):

    def save_run(self, result: DecisionResult) -> None:
        ...

    def get_run(self, decision_id: str) -> DecisionResult | None:
        ...

    def list_runs(
        self, query: DecisionQuery | None = None,
    ) -> list[DecisionResult]:
        ...

    def save_outcome(self, outcome: OutcomeRecord) -> None:
        ...

    def get_outcomes(self, decision_id: str) -> list[OutcomeRecord]:
        ...
