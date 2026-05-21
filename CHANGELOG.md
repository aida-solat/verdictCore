# Changelog

All notable changes to VerdictCore will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-05-21

### Added

- **Decision Memory** — structured decision history summarization with domain filtering
- **Pattern Discovery** — detect fragility patterns, constraint failure patterns from history
- **Evidence Calibration** — outcome-based source reliability profiling and adjustment suggestions
- **Policy Drift Detection** — identify outcome drift and constraint drift over time
- **Adaptive Policy Suggestions** — human-controlled policy improvement proposals with guardrails
- **Cross-Domain Transfer** — identify transferable patterns between decision domains
- **CLI Commands** — `verdict memory`, `verdict patterns`, `verdict drift`, `verdict adaptive`
- **Tests** — 20 new tests (163 total passing)

## [0.4.0] - 2026-05-21

### Added

- **Simulation Variable Model** — support for uncertain values with distributions (normal, triangular, uniform, beta, categorical)
- **Monte Carlo Simulation** — run decisions thousands of times, compute winner distribution, risk metrics (P90, overrun probability)
- **Stress Testing Engine** — perturbation-based stress scenarios with configurable shocks
- **Multi-Objective Optimization** — Pareto frontier computation and dominance analysis
- **Constraint Optimization** — threshold sweep analysis with cost/risk trade-off evaluation
- **Decision Portfolio Simulation** — simulate policy impact across historical decision sets
- **CLI Commands** — `verdict simulate`, `verdict stress-test`, `verdict optimize`, `verdict constraint-optimize`, `verdict portfolio`
- **Tests** — 29 new tests (143 total passing)

## [0.3.0] - 2026-05-21

### Added

- **Policy Versioning & Diff** — version policies, compute diffs between versions
- **Human Review & Override** — append-only audited review events and overrides
- **Decision Registry** — SQLite-backed decision storage with query support
- **Decision DAGs** — multi-step decision graphs with dependency execution
- **Outcome Learning** — analyze historical outcomes to detect systematic patterns
- **Governance Rules** — configurable rules for requiring review/approval/escalation
- **Policy Recommendation Engine** — generate policy improvement suggestions
- **CLI Commands** — `verdict registry`, `verdict review`, `verdict graph`, `verdict governance`, `verdict learning`, `verdict policy`
- **Tests** — governance, registry, review, DAGs, learning, policies

## [0.2.0] - 2026-05-21

### Added

- **Scenario Engine** — run decisions under alternative policy assumptions, compute consistency
- **Value-of-Information** — identify highest-impact missing data with VoI scoring
- **Evidence Quality Scoring** — reliability, freshness, source type, overall quality assessment
- **Robustness Report** — stability, scenario consistency, data completeness, constraint risk
- **Outcome Tracking** — record actual outcomes and compare to predictions with quality scoring
- **CLI Commands** — `verdict scenarios`, `verdict voi`, `verdict evidence`, `verdict robustness`, `verdict outcome`
- **Tests** — scenarios, VoI, evidence quality, robustness, outcomes

## [0.1.0] - 2026-05-21

### Added

- **Core Engine** — `Deciwa` with full decision pipeline
- **Data Models** — `DecisionInput`, `DecisionResult`, `Criterion`, `Constraint`, `Alternative`, `Evidence`
- **Weighted Scoring** — min-max normalization with weight-based scoring
- **Constraint Evaluation** — block, warn, escalate actions with all comparison operators
- **Ranking** — automatic ranking with blocked alternative handling
- **Explanation System**
  - Why selected (natural language)
  - Why not (per alternative)
  - Top drivers (impact analysis)
  - Sensitivity analysis
  - Decision Stability Index
- **Audit Trail** — SHA-256 hash chain (input, ruleset, output), event ledger
- **IO Layer** — YAML loader, canonical JSON exporter, Markdown report exporter
- **CLI** — `verdict run`, `verdict validate`, `verdict explain`, `verdict version`
- **LLM Boundary** — interface and enforcement (stub for v0.1, full in v0.5)
- **Missing Data Policies** — penalize, ignore, needs_review
- **Decision Statuses** — decided, blocked, needs_review, insufficient_data, error
- **Examples** — AI model selection, supplier selection, cloud vendor selection
- **Test Suite** — engine, scoring, constraints, explanations, sensitivity, audit, YAML loader
- **Apache 2.0 License**
