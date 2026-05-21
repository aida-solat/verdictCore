"""Tests for Human Review & Override."""

from verdictcore.review import OverrideEvent, ReviewState


class TestReviewState:

    def test_initial_state(self):
        state = ReviewState(decision_id="d001")
        assert state.status == "not_required"

    def test_require_review(self):
        state = ReviewState(decision_id="d001")
        state.require_review("Fragile decision", required_by="system")
        assert state.status == "required"
        assert state.reason == "Fragile decision"

    def test_approve(self):
        state = ReviewState(decision_id="d001")
        state.require_review("Needs check")
        state.approve("reviewer_01")
        assert state.status == "approved"
        assert len(state.comments) == 1

    def test_reject(self):
        state = ReviewState(decision_id="d001")
        state.require_review("Needs check")
        state.reject("reviewer_01", "Insufficient evidence")
        assert state.status == "rejected"

    def test_override(self):
        state = ReviewState(decision_id="d001")
        event = OverrideEvent(
            decision_id="d001",
            actor_id="cfo",
            actor_role="financial_approver",
            previous_recommendation="supplier_b",
            new_recommendation="manual_review_required",
            reason="Unresolved legal dispute.",
        )
        state.override(event)
        assert state.status == "overridden"
        assert len(state.overrides) == 1
        assert state.overrides[0].audit_hash is not None

    def test_escalate(self):
        state = ReviewState(decision_id="d001")
        state.escalate("Spend exceeds threshold")
        assert state.status == "escalated"

    def test_override_audit_hash(self):
        event = OverrideEvent(
            decision_id="d001",
            actor_id="reviewer",
            reason="Test override",
            new_recommendation="reject",
        )
        assert event.audit_hash is not None
        assert len(event.audit_hash) == 16
