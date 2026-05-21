# Audit Model

## Overview

Every VerdictCore decision produces a tamper-evident audit trail. This enables:

- **Reproducibility** — re-run any decision and verify identical output
- **Compliance** — prove that rules were followed
- **Tamper detection** — detect if input or output was modified post-hoc

## Hash Chain

Each DecisionResult contains three hashes:

| Hash | What It Covers |
|------|---------------|
| `input_hash` | SHA-256 of the canonical JSON of DecisionInput |
| `ruleset_hash` | SHA-256 of criteria + constraints + policy version |
| `output_hash` | SHA-256 of the result (excluding the audit field itself) |

### Verification

```python
from verdictcore.audit import compute_input_hash

# Re-compute and compare
original_hash = result.audit.input_hash
recomputed_hash = compute_input_hash(decision_input.model_dump(mode="json"))

assert original_hash == recomputed_hash  # Input unchanged
```

## Event Ledger

The engine maintains an internal event chain during execution:

```json
[
  {"event_type": "decision_run_created", "hash": "sha256:abc", "prev_hash": null},
  {"event_type": "constraints_evaluated", "hash": "sha256:def", "prev_hash": "sha256:abc"},
  {"event_type": "scoring_completed", "hash": "sha256:ghi", "prev_hash": "sha256:def"},
  {"event_type": "decision_generated", "hash": "sha256:jkl", "prev_hash": "sha256:ghi"},
  {"event_type": "audit_finalized", "hash": "sha256:mno", "prev_hash": "sha256:jkl"}
]
```

Each event references the previous event's hash, forming a chain. Breaking any link is detectable.

## Reproducibility Verification

```python
from verdictcore.audit.reproducibility import verify_reproducibility

result1 = engine.run(decision_input)
result2 = engine.run(decision_input)

check = verify_reproducibility(result1.audit, result2.audit)
assert check["fully_reproducible"] is True
```

## What Makes This Enterprise-Grade

1. **No database required** — hashes are in the result JSON itself
2. **Self-verifying** — any result can verify itself offline
3. **Lightweight** — no blockchain, no distributed consensus
4. **Standard** — SHA-256, canonical JSON, ISO timestamps
