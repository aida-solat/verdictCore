"""SHA-256 hashing for audit integrity."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha256(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_input_hash(decision_input_dict: dict[str, Any]) -> str:
    canonical = _canonical_json(decision_input_dict)
    return _sha256(canonical)


def compute_ruleset_hash(
    criteria_dicts: list[dict[str, Any]],
    constraint_dicts: list[dict[str, Any]],
    policy_version: str,
) -> str:
    ruleset = {
        "criteria": criteria_dicts,
        "constraints": constraint_dicts,
        "policy_version": policy_version,
    }
    canonical = _canonical_json(ruleset)
    return _sha256(canonical)


def compute_output_hash(result_dict: dict[str, Any]) -> str:
    output_data = {k: v for k, v in result_dict.items() if k != "audit"}
    canonical = _canonical_json(output_data)
    return _sha256(canonical)
