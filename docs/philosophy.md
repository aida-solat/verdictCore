# Philosophy

## Rules Decide. LLMs Assist.

VerdictCore is built on a single principle: **decisions must be deterministic, explainable, and auditable**.

### The Problem

Modern AI systems are powerful — but they are probabilistic. When you ask an LLM to "choose the best option," you get:

- Non-reproducible results
- No audit trail
- No constraint enforcement
- No sensitivity analysis
- No way to explain "why not X?"

This is fine for creative writing. It is **unacceptable** for enterprise decisions.

### The Solution

VerdictCore separates the **decision logic** (deterministic) from the **language layer** (probabilistic).

```
┌────────────────────────────┐
│    Deterministic Core      │  ← Rules, weights, constraints
│    (VerdictCore Engine)    │     Same input = same output
└────────────────────────────┘
            ↓
┌────────────────────────────┐
│    Optional LLM Layer      │  ← Narrative, evidence extraction
│    (Read-only access)      │     Cannot modify decisions
└────────────────────────────┘
```

### Design Principles

1. **Determinism over stochasticity** — Given the same input, the engine must always produce the same output.

2. **Explainability is not optional** — Every decision must explain itself: why this option, why not that one, what drove the outcome.

3. **Audit by default** — Every decision produces a hash chain. No extra configuration needed.

4. **Constraints are sacred** — No system (including LLMs) can override a constraint. If something is blocked, it stays blocked.

5. **Human-in-the-loop native** — VerdictCore assists human decision-makers. It does not replace them.

6. **Composable and minimal** — Small, focused modules. No monolith. No magic.

### Who This Is For

- AI Engineers building decision pipelines
- Backend Engineers structuring complex business logic
- Enterprise Architects needing audit and governance
- Procurement / Risk / Compliance teams
- Anyone tired of "vibes-based AI decisions"
