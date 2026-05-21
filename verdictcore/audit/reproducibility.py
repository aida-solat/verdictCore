"""Reproducibility verification."""

from __future__ import annotations

from verdictcore.models.result import AuditSummary


def verify_reproducibility(
    original_audit: AuditSummary,
    rerun_audit: AuditSummary,
) -> dict[str, bool]:
    return {
        "input_match": original_audit.input_hash == rerun_audit.input_hash,
        "ruleset_match": original_audit.ruleset_hash == rerun_audit.ruleset_hash,
        "output_match": original_audit.output_hash == rerun_audit.output_hash,
        "fully_reproducible": (
            original_audit.input_hash == rerun_audit.input_hash
            and original_audit.ruleset_hash == rerun_audit.ruleset_hash
            and original_audit.output_hash == rerun_audit.output_hash
        ),
    }
