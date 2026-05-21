"""SQLite-based decision registry."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from verdictcore.models.intelligence import OutcomeRecord
from verdictcore.models.result import DecisionResult
from verdictcore.registry.store import DecisionQuery

_SCHEMA = """
CREATE TABLE IF NOT EXISTS decision_runs (
    decision_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    status TEXT NOT NULL,
    selected_alternative_id TEXT,
    policy_version TEXT,
    created_at TEXT,
    input_hash TEXT,
    output_hash TEXT,
    result_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outcomes (
    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL,
    selected_alternative_id TEXT,
    recorded_at TEXT,
    quality_level TEXT,
    outcome_json TEXT NOT NULL,
    FOREIGN KEY (decision_id) REFERENCES decision_runs(decision_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_domain ON decision_runs(domain);
CREATE INDEX IF NOT EXISTS idx_outcomes_decision ON outcomes(decision_id);
"""


class SQLiteDecisionRegistry:

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def save_run(self, result: DecisionResult) -> None:
        result_json = result.model_dump_json()
        self._conn.execute(
            """
            INSERT OR REPLACE INTO decision_runs
            (decision_id, domain, status, selected_alternative_id,
             policy_version, created_at, input_hash, output_hash, result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.decision_id,
                result.domain,
                result.status.value,
                result.recommendation.selected_alternative_id,
                result.audit.policy_version,
                result.audit.created_at.isoformat(),
                result.audit.input_hash,
                result.audit.output_hash,
                result_json,
            ),
        )
        self._conn.commit()

    def get_run(self, decision_id: str) -> DecisionResult | None:
        row = self._conn.execute(
            "SELECT result_json FROM decision_runs WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()
        if row is None:
            return None
        return DecisionResult.model_validate_json(row["result_json"])

    def list_runs(
        self, query: DecisionQuery | None = None,
    ) -> list[DecisionResult]:
        sql = "SELECT result_json FROM decision_runs"
        params: list[str] = []
        conditions: list[str] = []

        if query:
            if query.domain:
                conditions.append("domain = ?")
                params.append(query.domain)
            if query.status:
                conditions.append("status = ?")
                params.append(query.status)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC"

        if query:
            sql += f" LIMIT {query.limit}"
        else:
            sql += " LIMIT 100"

        rows = self._conn.execute(sql, params).fetchall()
        return [
            DecisionResult.model_validate_json(r["result_json"])
            for r in rows
        ]

    def save_outcome(self, outcome: OutcomeRecord) -> None:
        outcome_json = outcome.model_dump_json()
        self._conn.execute(
            """
            INSERT INTO outcomes
            (decision_id, selected_alternative_id, recorded_at,
             quality_level, outcome_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                outcome.decision_id,
                outcome.selected_alternative_id,
                outcome.recorded_at.isoformat(),
                None,
                outcome_json,
            ),
        )
        self._conn.commit()

    def get_outcomes(self, decision_id: str) -> list[OutcomeRecord]:
        rows = self._conn.execute(
            "SELECT outcome_json FROM outcomes WHERE decision_id = ?",
            (decision_id,),
        ).fetchall()
        return [
            OutcomeRecord.model_validate_json(r["outcome_json"])
            for r in rows
        ]

    def count_runs(self, domain: str | None = None) -> int:
        if domain:
            row = self._conn.execute(
                "SELECT COUNT(*) as cnt FROM decision_runs WHERE domain = ?",
                (domain,),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) as cnt FROM decision_runs",
            ).fetchone()
        return row["cnt"] if row else 0

    def close(self) -> None:
        self._conn.close()
