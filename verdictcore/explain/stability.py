"""Stability index interpretation."""

from __future__ import annotations

from verdictcore.models.result import SensitivityResult


def compute_stability_index(sensitivity: SensitivityResult) -> str:
    score = sensitivity.decision_stability_score
    level = sensitivity.level

    if level == "stable":
        interpretation = (
            f"The decision is highly stable (score: {score:.2f}). "
            f"Weight changes are unlikely to alter the outcome."
        )
    elif level == "moderately_stable":
        sensitive_str = (
            ", ".join(sensitivity.sensitive_to[:3])
            if sensitivity.sensitive_to else "some criteria"
        )
        interpretation = (
            f"The decision is reasonably stable (score: {score:.2f}) "
            f"but sensitive to {sensitive_str} weights."
        )
    elif level == "fragile":
        sensitive_str = (
            ", ".join(sensitivity.sensitive_to[:3])
            if sensitivity.sensitive_to else "multiple criteria"
        )
        interpretation = (
            f"The decision is fragile (score: {score:.2f}). "
            f"Small changes in {sensitive_str} could flip the outcome. "
            f"Consider gathering more evidence or reviewing weights."
        )
    else:
        interpretation = (
            f"The decision is unstable (score: {score:.2f}). "
            f"The current winner is not strongly dominant. "
            f"Human review is recommended before acting on this result."
        )

    return interpretation
