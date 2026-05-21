# VerdictCore

**Deterministic decisions. Explainable tradeoffs. Audit-ready outputs.**

Build decision engines where **rules decide** and **LLMs assist**.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.5.0-orange.svg)](CHANGELOG.md)

---

## Why VerdictCore?

Modern AI systems generate answers — but enterprises need **decisions** that are:

- **Structured** — formal decision objects, not ad-hoc prompts
- **Explainable** — why this? why not that? what drives the outcome?
- **Reproducible** — same input → same output, every time
- **Auditable** — full hash chain, tamper-evident, compliance-ready
- **Simulatable** — Monte Carlo, stress tests, Pareto trade-offs
- **Governable** — policies, reviews, registries, drift detection

VerdictCore fills the gap between AI tools that generate text and enterprise systems that need **governed, deterministic decisions**.

---

## Install

```bash
pip install verdictcore
```

For development:

```bash
pip install verdictcore[dev]
```

---

## Quickstart

### CLI

```bash
# Run a decision
verdict run examples/ai_model_selection/decision.yaml

# Run with output
verdict run decision.yaml --output result.json --report report.md

# Validate input
verdict validate decision.yaml

# Simulate under uncertainty
verdict simulate decision.yaml --iterations 5000

# Stress-test a decision
verdict stress-test decision.yaml

# Detect policy drift
verdict drift --registry verdictcore.db --policy my_policy
```

### Python SDK

```python
from verdictcore import Deciwa
from verdictcore.io import load_decision_yaml

decision_input = load_decision_yaml("examples/ai_model_selection/decision.yaml")

engine = Deciwa()
result = engine.run(decision_input)

print(result.recommendation.selected_alternative_name)  # "Claude Sonnet"
print(result.explanation.why_selected)
print(result.why_not("model_a"))
print(result.to_canonical_json())
```

### Programmatic

```python
from verdictcore import Deciwa, DecisionInput, Criterion, Constraint, Alternative

decision = DecisionInput(
    question="Which cloud provider for our platform?",
    domain="cloud_vendor_selection",
    criteria=[
        Criterion(name="cost", weight=0.25, direction="minimize"),
        Criterion(name="reliability", weight=0.30, direction="maximize"),
        Criterion(name="security", weight=0.25, direction="maximize"),
        Criterion(name="developer_experience", weight=0.20, direction="maximize"),
    ],
    constraints=[
        Constraint(field="security", operator=">=", value=80, action="block"),
    ],
    alternatives=[
        Alternative(id="aws", name="AWS", values={"cost": 72, "reliability": 95, "security": 92, "developer_experience": 82}),
        Alternative(id="gcp", name="GCP", values={"cost": 68, "reliability": 93, "security": 88, "developer_experience": 90}),
        Alternative(id="azure", name="Azure", values={"cost": 75, "reliability": 91, "security": 90, "developer_experience": 78}),
    ],
)

engine = Deciwa()
result = engine.run(decision)

print(result.selected.name)
print(result.explanation.sensitivity.level)
```

---

## Core Concepts

| Concept           | Description                                                   |
| ----------------- | ------------------------------------------------------------- |
| **DecisionInput** | Complete input: question, criteria, constraints, alternatives |
| **DecisionRun**   | One execution of the engine on a DecisionInput                |
| **Criterion**     | What matters — name, weight, direction (maximize/minimize)    |
| **Constraint**    | Hard/soft rules — block, warn, or escalate                    |
| **Alternative**   | A candidate option with scored values                         |
| **Evidence**      | Supporting data for values (source, confidence, reliability)  |
| **Explanation**   | Why selected, why not, top drivers, sensitivity               |
| **Audit Trail**   | Input hash, ruleset hash, output hash — tamper-evident        |

---

## Decision Statuses

| Status              | Meaning                                |
| ------------------- | -------------------------------------- |
| `decided`           | Winner selected — all good             |
| `blocked`           | All alternatives failed constraints    |
| `needs_review`      | Missing data or escalation triggered   |
| `insufficient_data` | Cannot score — critical values missing |
| `error`             | Runtime or schema problem              |

---

## LLM Boundary

> **Rules decide. LLMs assist.**

This is the core principle of VerdictCore.

**LLMs ARE allowed to:**

- Generate narrative summaries
- Extract structured evidence from text
- Suggest missing information
- Explain results in natural language

**LLMs are NOT allowed to:**

- Modify final scores
- Override constraints
- Select winners without deterministic evaluation
- Generate unaudited recommendations

---

## Example Output

```
VerdictCore DecisionRun
───────────────────────

Decision: Which AI model should we use for a healthcare RAG system?
Status: decided
Selected: Claude Sonnet
Confidence: 0.82

Rankings:
  1. Claude Sonnet  — 84.7
  2. Llama 4        — 79.3
  —  GPT-4.1       — BLOCKED

Constraint Violations:
  • GPT-4.1: privacy >= 85 (actual: 70) → block
  • GPT-4.1: compliance >= 90 (actual: 75) → block

Why Selected:
  Claude Sonnet was selected because it passed all mandatory constraints
  and achieved the highest weighted score (84.7).

Decision Stability: moderately_stable (0.74)
```

---

## Features

### v0.1 — Core Engine

- [x] Pydantic data models (DecisionInput, Result, Criterion, Constraint, Alternative, Evidence)
- [x] Weighted scoring with min-max normalization
- [x] Constraint evaluation (block / warn / escalate)
- [x] Ranking with blocked alternative handling
- [x] Explanation: why selected, why not, top drivers
- [x] Sensitivity analysis & Decision Stability Index
- [x] Audit trail: SHA-256 hash chain (input, ruleset, output)
- [x] YAML input format & canonical JSON output
- [x] Markdown report export
- [x] CLI (`verdict run`, `verdict validate`, `verdict explain`)

### v0.2 — Decision Intelligence

- [x] Scenario Engine — run decisions under alternative policies
- [x] Value-of-Information — identify highest-impact missing data
- [x] Evidence Quality Scoring — reliability, freshness, source type
- [x] Robustness Report — stability, consistency, data completeness
- [x] Outcome Tracking — record actual outcomes and compare to predictions

### v0.3 — Decision Governance

- [x] Policy Versioning & Diff — version policies, compare changes
- [x] Human Review & Override — append-only audited overrides
- [x] Decision Registry — SQLite-backed storage and query
- [x] Decision DAGs — multi-step decision graphs with dependencies
- [x] Outcome Learning — detect patterns from historical outcomes
- [x] Governance Rules — require review/approval/escalation based on conditions

### v0.4 — Simulation & Optimization

- [x] Simulation Variables — uncertain values with statistical distributions
- [x] Monte Carlo Simulation — winner distribution, risk metrics, P90
- [x] Stress Testing — perturbation-based scenario shocks
- [x] Multi-Objective Optimization — Pareto frontier, dominance analysis
- [x] Constraint Optimization — threshold sweep with cost/risk trade-offs
- [x] Decision Portfolio Simulation — policy impact across historical decisions

### v0.5 — Adaptive Decision Network

- [x] Decision Memory — structured history summarization
- [x] Pattern Discovery — detect fragility, constraint failures, overrides
- [x] Evidence Calibration — outcome-based source reliability adjustment
- [x] Policy Drift Detection — identify when policies become stale
- [x] Adaptive Policy Suggestions — human-controlled improvement proposals
- [x] Cross-Domain Transfer — apply patterns across decision domains

---

## CLI Commands

```bash
# Core
verdict run <file>                    # Run a decision
verdict validate <file>               # Validate YAML input
verdict explain <file>                # Show full explanation

# Intelligence (v0.2)
verdict scenarios <file>              # Scenario analysis
verdict voi <file>                    # Value-of-information report
verdict robustness <file>             # Robustness report

# Governance (v0.3)
verdict registry add <file>           # Add decision to registry
verdict registry list                 # List stored decisions
verdict graph run <file>              # Execute decision DAG

# Simulation (v0.4)
verdict simulate <file>               # Monte Carlo simulation
verdict stress-test <file>            # Stress testing
verdict optimize <file>               # Pareto optimization
verdict constraint-optimize <file>    # Constraint threshold sweep
verdict portfolio simulate            # Portfolio-level simulation

# Adaptive (v0.5)
verdict memory --registry <db>        # Decision memory summary
verdict patterns --registry <db>      # Pattern discovery
verdict drift --registry <db>         # Policy drift detection
verdict adaptive --registry <db>      # Policy suggestions
```

---

## Roadmap

| Version    | Focus                     | Status  |
| ---------- | ------------------------- | ------- |
| **v0.1**   | Core Engine               | ✅ Done |
| **v0.2**   | Decision Intelligence     | ✅ Done |
| **v0.3**   | Decision Governance       | ✅ Done |
| **v0.4**   | Simulation & Optimization | ✅ Done |
| **v0.5**   | Adaptive Decision Network | ✅ Done |
| **Future** | Adaptive Decision Systems | Planned |

---

## Project Structure

```
verdictcore/
├── verdictcore/
│   ├── engine.py          # Main Deciwa engine
│   ├── models/            # Pydantic data models
│   ├── scoring/           # Weighted scoring, normalization, ranking
│   ├── constraints/       # Constraint evaluator
│   ├── explain/           # Explainability (drivers, why_not, sensitivity)
│   ├── audit/             # Hashing, ledger, reproducibility
│   ├── io/                # YAML loader, JSON/Markdown exporters
│   ├── llm/               # LLM boundary, narrative interface
│   ├── scenarios/         # Scenario engine
│   ├── voi/               # Value-of-information analysis
│   ├── evidence/          # Evidence quality scoring
│   ├── robustness/        # Robustness report
│   ├── outcomes/          # Outcome tracking
│   ├── policies/          # Policy versioning & diff
│   ├── review/            # Human review & override
│   ├── registry/          # Decision registry (SQLite)
│   ├── dags/              # Decision DAGs
│   ├── learning/          # Outcome learning
│   ├── governance/        # Governance rules
│   ├── simulation/        # Monte Carlo simulation
│   ├── stress/            # Stress testing
│   ├── optimization/      # Pareto & constraint optimization
│   ├── portfolio/         # Portfolio simulation
│   ├── memory/            # Decision memory
│   ├── patterns/          # Pattern discovery
│   ├── calibration/       # Evidence calibration
│   ├── drift/             # Policy drift detection
│   ├── adaptive/          # Adaptive policy suggestions
│   ├── transfer/          # Cross-domain transfer
│   └── cli.py             # Typer CLI (25 commands)
├── examples/              # Ready-to-run decision YAML files
├── tests/                 # 163 tests across 28 test files
├── docs/                  # Documentation
└── pyproject.toml         # Package configuration
```

---

## Contributing

Contributions welcome. Please:

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest`
4. Run linter: `ruff check verdictcore tests`
5. Submit a PR

---

## License

Apache 2.0 — see [LICENSE](LICENSE)

---

## Philosophy

> _"AI should help humans make better decisions — not make decisions for them."_

VerdictCore exists because deterministic infrastructure deserves the same rigor we give to databases, compilers, and type systems. Decisions are too important to leave to probabilistic guesswork.

**Build decision engines where rules decide and LLMs assist.**
