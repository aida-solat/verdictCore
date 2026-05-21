"""Core decision engine."""

from __future__ import annotations

import uuid

from verdictcore.audit.hashing import (
    compute_input_hash,
    compute_output_hash,
    compute_ruleset_hash,
)
from verdictcore.audit.ledger import AuditLedger
from verdictcore.constraints.evaluator import ConstraintEvaluator
from verdictcore.explain.drivers import compute_top_drivers
from verdictcore.explain.sensitivity import run_sensitivity_analysis
from verdictcore.explain.why_not import generate_why_not
from verdictcore.explain.why_selected import generate_why_selected
from verdictcore.models.decision import DecisionInput
from verdictcore.models.policy import MissingPolicy
from verdictcore.models.result import (
    AuditSummary,
    DecisionResult,
    DecisionStatus,
    Explanation,
    Recommendation,
)
from verdictcore.scoring.ranking import rank_alternatives
from verdictcore.scoring.weighted import WeightedScorer
from verdictcore.version import __version__


class Deciwa:
    """Evaluates structured decision inputs and produces deterministic, auditable results."""

    def __init__(self, enable_sensitivity: bool = True) -> None:
        self.enable_sensitivity = enable_sensitivity

    def run(self, decision_input: DecisionInput) -> DecisionResult:
        """Execute a decision run and return a complete result with audit trail."""
        ledger = AuditLedger()
        ledger.record("decision_run_created", {"question": decision_input.question})

        decision_id = decision_input.decision_id or f"dec_{uuid.uuid4().hex[:12]}"

        constraint_evaluator = ConstraintEvaluator(
            decision_input.constraints, decision_input.alternatives
        )
        constraint_results = constraint_evaluator.evaluate()
        blocked_ids = constraint_evaluator.get_blocked_ids(constraint_results)
        warnings_map = constraint_evaluator.get_warnings_map(constraint_results)
        escalation_ids = constraint_evaluator.get_escalation_ids(constraint_results)

        ledger.record(
            "constraints_evaluated",
            {"blocked_count": str(len(blocked_ids)), "escalated_count": str(len(escalation_ids))},
        )

        all_blocked = len(blocked_ids) == len(decision_input.alternatives)
        scorer = WeightedScorer(
            decision_input.criteria,
            decision_input.alternatives,
            decision_input.missing_policy,
        )
        traces = scorer.score()

        ledger.record("scoring_completed", {"strategy": "weighted"})

        rankings = rank_alternatives(traces, blocked_ids, warnings_map)

        status, recommendation = self._determine_outcome(
            rankings=rankings,
            all_blocked=all_blocked,
            has_missing_data=scorer.has_missing_data,
            missing_policy=decision_input.missing_policy,
            escalation_ids=escalation_ids,
        )

        ledger.record("decision_generated", {"status": status.value})

        winner = next((r for r in rankings if r.rank == 1), None)

        if winner and winner.calculation_trace:
            top_drivers = compute_top_drivers(winner.calculation_trace)
            why_selected = generate_why_selected(winner, rankings, constraint_results)
            why_not = generate_why_not(winner, rankings, constraint_results)
        else:
            top_drivers = []
            why_selected = self._no_winner_explanation(status)
            why_not = []

        sensitivity = None
        if self.enable_sensitivity and winner and not all_blocked:
            sensitivity = run_sensitivity_analysis(
                criteria=decision_input.criteria,
                alternatives=decision_input.alternatives,
                blocked_ids=blocked_ids,
                winner_id=winner.alternative_id,
                missing_policy=decision_input.missing_policy,
            )

        explanation = Explanation(
            why_selected=why_selected,
            top_drivers=top_drivers,
            why_not=why_not,
            sensitivity=sensitivity,
        )

        input_dict = decision_input.model_dump(mode="json")
        input_hash = compute_input_hash(input_dict)
        ruleset_hash = compute_ruleset_hash(
            criteria_dicts=[c.model_dump(mode="json") for c in decision_input.criteria],
            constraint_dicts=[c.model_dump(mode="json") for c in decision_input.constraints],
            policy_version=decision_input.policy_version,
        )

        audit = AuditSummary(
            engine_version=__version__,
            policy_version=decision_input.policy_version,
            input_hash=input_hash,
            ruleset_hash=ruleset_hash,
            output_hash="",
        )

        warnings: list[str] = []
        for alt_id, alt_warnings in warnings_map.items():
            warnings.extend(alt_warnings)
        if scorer.has_missing_data and decision_input.missing_policy == MissingPolicy.NEEDS_REVIEW:
            warnings.append("Some alternatives have missing data. Review recommended.")

        result = DecisionResult(
            decision_id=decision_id,
            domain=decision_input.domain,
            question=decision_input.question,
            status=status,
            recommendation=recommendation,
            rankings=rankings,
            constraint_results=constraint_results,
            explanation=explanation,
            audit=audit,
            warnings=warnings,
            metadata=decision_input.metadata,
        )

        result_dict = result.model_dump(mode="json")
        output_hash = compute_output_hash(result_dict)
        result.audit.output_hash = output_hash

        ledger.record("audit_finalized", {"output_hash": output_hash})

        return result

    def _determine_outcome(
        self,
        rankings: list,
        all_blocked: bool,
        has_missing_data: bool,
        missing_policy: MissingPolicy,
        escalation_ids: set[str],
    ) -> tuple[DecisionStatus, Recommendation]:

        if all_blocked:
            return (
                DecisionStatus.BLOCKED,
                Recommendation(
                    decision_class="reject",
                    confidence=1.0,
                ),
            )

        if has_missing_data and missing_policy == MissingPolicy.NEEDS_REVIEW:
            winner = next((r for r in rankings if r.rank == 1), None)
            if winner:
                return (
                    DecisionStatus.NEEDS_REVIEW,
                    Recommendation(
                        selected_alternative_id=winner.alternative_id,
                        selected_alternative_name=winner.name,
                        decision_class="escalate",
                        confidence=0.5,
                    ),
                )
            return (
                DecisionStatus.INSUFFICIENT_DATA,
                Recommendation(decision_class="no_selection", confidence=0.0),
            )

        eligible = [r for r in rankings if not r.blocked]
        if eligible and eligible[0].alternative_id in escalation_ids:
            winner = eligible[0]
            return (
                DecisionStatus.NEEDS_REVIEW,
                Recommendation(
                    selected_alternative_id=winner.alternative_id,
                    selected_alternative_name=winner.name,
                    decision_class="escalate",
                    confidence=0.6,
                ),
            )

        winner = next((r for r in rankings if r.rank == 1), None)
        if winner:
            runners = [r for r in rankings if not r.blocked and r.rank and r.rank > 1]
            if runners and winner.total_score > 0:
                gap_ratio = (winner.total_score - runners[0].total_score) / winner.total_score
                confidence = min(0.95, 0.6 + gap_ratio)
            else:
                confidence = 0.9

            return (
                DecisionStatus.DECIDED,
                Recommendation(
                    selected_alternative_id=winner.alternative_id,
                    selected_alternative_name=winner.name,
                    decision_class="approve",
                    confidence=round(confidence, 2),
                ),
            )

        return (
            DecisionStatus.ERROR,
            Recommendation(decision_class="no_selection", confidence=0.0),
        )

    @staticmethod
    def _no_winner_explanation(status: DecisionStatus) -> str:
        if status == DecisionStatus.BLOCKED:
            return (
                "All alternatives were blocked due to constraint violations."
                " No selection possible."
            )
        elif status == DecisionStatus.INSUFFICIENT_DATA:
            return (
                "Insufficient data to make a deterministic decision."
                " Please provide missing values."
            )
        elif status == DecisionStatus.ERROR:
            return "An error occurred during decision evaluation."
        return "No selection was made."
