"""Tests for audit hashing and ledger."""


from verdictcore.audit.hashing import (
    compute_input_hash,
    compute_output_hash,
    compute_ruleset_hash,
)
from verdictcore.audit.ledger import AuditLedger


class TestAuditHashing:
    def test_input_hash_deterministic(self):
        data = {"question": "test", "alternatives": [{"id": "a"}]}
        h1 = compute_input_hash(data)
        h2 = compute_input_hash(data)
        assert h1 == h2

    def test_input_hash_changes_with_data(self):
        data1 = {"question": "test1"}
        data2 = {"question": "test2"}
        assert compute_input_hash(data1) != compute_input_hash(data2)

    def test_hash_format(self):
        h = compute_input_hash({"x": 1})
        assert h.startswith("sha256:")
        assert len(h) == len("sha256:") + 64  # SHA-256 is 64 hex chars

    def test_ruleset_hash(self):
        h = compute_ruleset_hash(
            criteria_dicts=[{"name": "x", "weight": 0.5}],
            constraint_dicts=[{"field": "x", "operator": ">=", "value": 10}],
            policy_version="v1",
        )
        assert h.startswith("sha256:")

    def test_output_hash_excludes_audit(self):
        result_dict = {
            "decision_id": "test",
            "status": "decided",
            "audit": {"input_hash": "sha256:abc"},
        }
        h = compute_output_hash(result_dict)
        assert h.startswith("sha256:")


class TestAuditLedger:
    def test_empty_ledger(self):
        ledger = AuditLedger()
        assert len(ledger.events) == 0
        assert ledger.verify_chain() is True

    def test_single_event(self):
        ledger = AuditLedger()
        event = ledger.record("test_event")
        assert event.event_type == "test_event"
        assert event.prev_hash is None
        assert event.hash.startswith("sha256:")

    def test_chain_integrity(self):
        ledger = AuditLedger()
        ledger.record("event_1")
        ledger.record("event_2")
        ledger.record("event_3")
        assert ledger.verify_chain() is True
        # Second event should reference first
        assert ledger.events[1].prev_hash == ledger.events[0].hash

    def test_chain_tamper_detection(self):
        ledger = AuditLedger()
        ledger.record("event_1")
        ledger.record("event_2")
        # Tamper with the chain
        ledger.events[1].prev_hash = "sha256:fake"
        assert ledger.verify_chain() is False
