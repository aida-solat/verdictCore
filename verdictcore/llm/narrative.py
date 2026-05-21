"""Template-based narrative generation."""

from __future__ import annotations

from verdictcore.models.result import DecisionResult


def generate_template_narrative(result: DecisionResult) -> str:
    lines: list[str] = []

    lines.append("## Decision Summary\n")
    lines.append(f"**Question:** {result.question}\n")

    if result.recommendation.selected_alternative_name:
        lines.append(
            f"**Recommendation:** {result.recommendation.selected_alternative_name} "
            f"was selected with {result.recommendation.confidence:.0%} confidence.\n"
        )
    else:
        lines.append(f"**Status:** {result.status.value} — no alternative was selected.\n")

    lines.append(f"**Rationale:** {result.explanation.why_selected}\n")

    if result.explanation.top_drivers:
        drivers = ", ".join(d.criterion for d in result.explanation.top_drivers[:3])
        lines.append(f"**Key factors:** {drivers}\n")

    if result.explanation.sensitivity:
        lines.append(
            f"**Stability:** This decision is {result.explanation.sensitivity.level} "
            f"(score: {result.explanation.sensitivity.decision_stability_score:.2f}).\n"
        )

    if result.warnings:
        lines.append(f"**Warnings:** {'; '.join(result.warnings)}\n")

    return "\n".join(lines)
