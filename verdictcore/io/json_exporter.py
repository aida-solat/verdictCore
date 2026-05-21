"""JSON export."""

from __future__ import annotations

import json
from pathlib import Path

from verdictcore.models.result import DecisionResult


def export_json(result: DecisionResult, path: str | Path | None = None) -> str:
    json_str = json.dumps(
        result.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )

    if path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_str, encoding="utf-8")

    return json_str
