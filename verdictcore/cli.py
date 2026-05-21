"""CLI interface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from verdictcore.engine import Deciwa
from verdictcore.io.json_exporter import export_json
from verdictcore.io.markdown_exporter import export_markdown
from verdictcore.io.yaml_loader import load_decision_yaml
from verdictcore.version import __version__

app = typer.Typer(
    name="verdict",
    help="VerdictCore — Deterministic decisions. Explainable tradeoffs. Audit-ready outputs.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def run(
    file: Path = typer.Argument(..., help="Path to decision YAML file"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output JSON file path",
    ),
    report: Optional[Path] = typer.Option(
        None, "--report", "-r", help="Output Markdown report path",
    ),
    no_sensitivity: bool = typer.Option(
        False, "--no-sensitivity", help="Skip sensitivity analysis",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
) -> None:
    """Run a decision evaluation from a YAML file."""
    try:
        decision_input = load_decision_yaml(file)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    engine = Deciwa(enable_sensitivity=not no_sensitivity)
    result = engine.run(decision_input)

    if not quiet:
        _print_result(result)

    if output:
        export_json(result, output)
        console.print(f"\n[green]JSON output saved to:[/green] {output}")

    if report:
        export_markdown(result, report)
        console.print(f"[green]Markdown report saved to:[/green] {report}")


@app.command()
def validate(
    file: Path = typer.Argument(..., help="Path to decision YAML file"),
) -> None:
    """Validate a decision YAML file without running it."""
    try:
        decision_input = load_decision_yaml(file)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Validation failed:[/red] {e}")
        raise typer.Exit(1)

    # Check weights sum
    weight_sum = sum(c.weight for c in decision_input.criteria)

    console.print(Panel.fit(
        f"[green]Valid decision file[/green]\n\n"
        f"Question: {decision_input.question}\n"
        f"Domain: {decision_input.domain}\n"
        f"Alternatives: {len(decision_input.alternatives)}\n"
        f"Criteria: {len(decision_input.criteria)}\n"
        f"Constraints: {len(decision_input.constraints)}\n"
        f"Weight sum: {weight_sum:.2f}",
        title="VerdictCore Validation",
    ))

    if abs(weight_sum - 1.0) > 0.01:
        console.print(
            f"[yellow]Warning:[/yellow] Criteria weights sum to"
            f" {weight_sum:.3f}, not 1.0"
        )


@app.command()
def explain(
    file: Path = typer.Argument(..., help="Path to decision output JSON file"),
) -> None:
    """Display explanation from a decision result JSON file."""
    import json

    from verdictcore.models.result import DecisionResult

    try:
        with open(file, "r") as f:
            data = json.load(f)
        result = DecisionResult(**data)
    except Exception as e:
        console.print(f"[red]Error loading result:[/red] {e}")
        raise typer.Exit(1)

    _print_explanation(result)


@app.command()
def scenarios(
    file: Path = typer.Argument(..., help="Path to decision YAML file"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output JSON file path",
    ),
) -> None:
    """Run scenario analysis against a decision YAML file."""
    import json

    from verdictcore.scenarios import ScenarioEngine

    try:
        decision_input = load_decision_yaml(file)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if not decision_input.scenarios:
        console.print("[yellow]No scenarios defined in YAML.[/yellow]")
        raise typer.Exit(0)

    engine = Deciwa(enable_sensitivity=False)
    base_result = engine.run(decision_input)
    se = ScenarioEngine(engine)
    results = se.run(decision_input, decision_input.scenarios)
    score = se.consistency_score(base_result, results)

    base_name = base_result.recommendation.selected_alternative_name or "none"
    console.print()
    console.print(Panel.fit(
        "[bold]Scenario Analysis[/bold]",
        subtitle=f"v{__version__}",
    ))
    console.print(f"\n[bold]Base winner:[/bold] {base_name}\n")
    console.print("[bold]Scenario winners:[/bold]")
    for sr in results:
        changed = " [yellow]CHANGED[/yellow]" if sr.changed_from_base else ""
        name = sr.selected_alternative_name or "none"
        console.print(f"  • {sr.scenario_name}: {name}{changed}")

    console.print(f"\n[bold]Consistency:[/bold] {score:.2f}")

    changed_count = sum(1 for r in results if r.changed_from_base)
    console.print(
        f"  Winner changed in {changed_count} of"
        f" {len(results)} scenario(s).\n"
    )

    if output:
        data = [r.model_dump(mode="json") for r in results]
        output.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        console.print(f"[green]Saved to:[/green] {output}")


@app.command()
def robustness(
    file: Path = typer.Argument(..., help="Path to decision YAML file"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output JSON file path",
    ),
) -> None:
    """Generate a decision robustness report."""
    from verdictcore.evidence import EvidenceQualityAnalyzer
    from verdictcore.robustness import RobustnessAnalyzer
    from verdictcore.scenarios import ScenarioEngine

    try:
        decision_input = load_decision_yaml(file)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    engine = Deciwa(enable_sensitivity=True)
    result = engine.run(decision_input)

    scenario_results = None
    if decision_input.scenarios:
        se = ScenarioEngine(engine)
        scenario_results = se.run(decision_input, decision_input.scenarios)

    eq_report = None
    if decision_input.evidence:
        eq_report = EvidenceQualityAnalyzer().evaluate(
            decision_input, result,
        )

    analyzer = RobustnessAnalyzer()
    report = analyzer.analyze(
        decision_input, result,
        scenario_results=scenario_results,
        evidence_quality_report=eq_report,
    )

    console.print()
    console.print(Panel.fit(
        "[bold]Decision Robustness Report[/bold]",
        subtitle=f"v{__version__}",
    ))
    name = result.recommendation.selected_alternative_name or "none"
    console.print(f"\n[bold]Selected:[/bold] {name}")
    console.print(
        f"[bold]Robustness:[/bold] {report.level}"
        f" ({report.overall_robustness_score:.2f})\n"
    )

    console.print("[bold]Breakdown:[/bold]")
    console.print(f"  Stability:            {report.stability_score:.2f}")
    console.print(
        f"  Scenario consistency: "
        f" {report.scenario_consistency_score:.2f}"
    )
    console.print(
        f"  Data completeness:    {report.data_completeness_score:.2f}"
    )
    console.print(
        f"  Evidence quality:     {report.evidence_quality_score:.2f}"
    )
    console.print(
        f"  Constraint risk:      {report.constraint_risk_score:.2f}"
    )
    console.print()

    if report.key_risks:
        console.print("[bold]Key Risks:[/bold]")
        for i, risk in enumerate(report.key_risks, 1):
            console.print(f"  {i}. {risk}")
        console.print()

    if report.recommendations:
        console.print("[bold]Recommendations:[/bold]")
        for rec in report.recommendations:
            console.print(f"  • {rec}")
        console.print()

    if output:
        import json
        output.write_text(json.dumps(
            report.model_dump(mode="json"), indent=2, ensure_ascii=False,
        ))
        console.print(f"[green]Saved to:[/green] {output}")


@app.command()
def voi(
    file: Path = typer.Argument(..., help="Path to decision YAML file"),
) -> None:
    """Run Value-of-Information analysis."""
    from verdictcore.voi import ValueOfInformationAnalyzer

    try:
        decision_input = load_decision_yaml(file)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    engine = Deciwa(enable_sensitivity=False)
    result = engine.run(decision_input)

    analyzer = ValueOfInformationAnalyzer()
    report = analyzer.analyze(decision_input, result)

    console.print()
    console.print(Panel.fit(
        "[bold]Value-of-Information Report[/bold]",
        subtitle=f"v{__version__}",
    ))

    if not report.items:
        console.print("\n[green]No missing information detected.[/green]\n")
        return

    console.print("\n[bold]Most valuable missing information:[/bold]\n")
    for i, item in enumerate(report.top_items[:10], 1):
        console.print(f"  {i}. [bold]{item.alternative_id}[/bold] → {item.field}")
        console.print(f"     Impact: {item.estimated_impact:.2f}")
        console.print(f"     {item.reason}")
        console.print(f"     Ask: [italic]{item.suggested_question}[/italic]")
        console.print()


@app.command(name="policy-diff")
def policy_diff(
    old_file: Path = typer.Argument(..., help="Path to old policy YAML"),
    new_file: Path = typer.Argument(..., help="Path to new policy YAML"),
) -> None:
    """Compare two policy versions and show differences."""
    import yaml

    from verdictcore.policies import DecisionPolicy, diff_policies

    try:
        with open(old_file, "r", encoding="utf-8") as f:
            old_data = yaml.safe_load(f)
        with open(new_file, "r", encoding="utf-8") as f:
            new_data = yaml.safe_load(f)
        old_policy = DecisionPolicy(**old_data)
        new_policy = DecisionPolicy(**new_data)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    diff = diff_policies(old_policy, new_policy)

    console.print()
    console.print(Panel.fit(
        "[bold]Policy Diff[/bold]",
        subtitle=f"v{__version__}",
    ))
    console.print(
        f"\n  {diff.from_policy} {diff.from_version}"
        f" → {diff.to_policy} {diff.to_version}\n"
    )

    if diff.criteria_changes:
        console.print("[bold]Criteria changes:[/bold]")
        for c in diff.criteria_changes:
            console.print(
                f"  • {c.criterion} ({c.field}):"
                f" {c.from_value} → {c.to_value}"
            )
        console.print()

    if diff.constraint_changes:
        console.print("[bold]Constraint changes:[/bold]")
        for c in diff.constraint_changes:
            console.print(f"  • [{c.change_type}] {c.field}")
            if c.from_value:
                console.print(f"    from: {c.from_value}")
            if c.to_value:
                console.print(f"    to:   {c.to_value}")
        console.print()

    if diff.interpretation:
        console.print("[bold]Interpretation:[/bold]")
        for note in diff.interpretation:
            console.print(f"  {note}")
        console.print()


@app.command(name="registry-add")
def registry_add(
    file: Path = typer.Argument(..., help="Path to decision result JSON"),
    db: Path = typer.Option(
        "verdictcore.db", "--db", help="Registry database path",
    ),
) -> None:
    """Add a decision result to the registry."""
    import json

    from verdictcore.models.result import DecisionResult
    from verdictcore.registry import SQLiteDecisionRegistry

    try:
        with open(file, "r") as f:
            data = json.load(f)
        result = DecisionResult(**data)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    registry = SQLiteDecisionRegistry(db)
    registry.save_run(result)
    registry.close()
    console.print(
        f"[green]Saved[/green] {result.decision_id} to {db}"
    )


@app.command(name="registry-list")
def registry_list(
    db: Path = typer.Option(
        "verdictcore.db", "--db", help="Registry database path",
    ),
    domain: Optional[str] = typer.Option(
        None, "--domain", help="Filter by domain",
    ),
) -> None:
    """List decision runs in the registry."""
    from verdictcore.registry import SQLiteDecisionRegistry
    from verdictcore.registry.store import DecisionQuery

    registry = SQLiteDecisionRegistry(db)
    query = DecisionQuery(domain=domain) if domain else None
    runs = registry.list_runs(query)
    registry.close()

    if not runs:
        console.print("[yellow]No runs found.[/yellow]")
        return

    table = Table(title="Decision Registry")
    table.add_column("ID")
    table.add_column("Domain")
    table.add_column("Status")
    table.add_column("Selected")

    for r in runs:
        table.add_row(
            r.decision_id,
            r.domain,
            r.status.value,
            r.recommendation.selected_alternative_name or "—",
        )
    console.print(table)


@app.command(name="registry-show")
def registry_show(
    decision_id: str = typer.Argument(..., help="Decision ID"),
    db: Path = typer.Option(
        "verdictcore.db", "--db", help="Registry database path",
    ),
) -> None:
    """Show a single decision run from the registry."""
    from verdictcore.registry import SQLiteDecisionRegistry

    registry = SQLiteDecisionRegistry(db)
    result = registry.get_run(decision_id)
    registry.close()

    if result is None:
        console.print(f"[red]Not found:[/red] {decision_id}")
        raise typer.Exit(1)

    _print_result(result)


@app.command(name="review-require")
def review_require(
    decision_id: str = typer.Argument(..., help="Decision ID"),
    reason: str = typer.Option(..., "--reason", "-r", help="Reason"),
) -> None:
    """Mark a decision as requiring review."""
    from verdictcore.review import ReviewState

    state = ReviewState(decision_id=decision_id)
    state.require_review(reason)
    console.print(
        f"[yellow]Review required[/yellow] for {decision_id}: {reason}"
    )


@app.command(name="review-override")
def review_override(
    decision_id: str = typer.Argument(..., help="Decision ID"),
    actor: str = typer.Option(..., "--actor", help="Actor ID"),
    reason: str = typer.Option(..., "--reason", "-r", help="Reason"),
    new_rec: Optional[str] = typer.Option(
        None, "--new", help="New recommendation",
    ),
) -> None:
    """Record an override event."""
    from verdictcore.review import OverrideEvent, ReviewState

    event = OverrideEvent(
        decision_id=decision_id,
        actor_id=actor,
        reason=reason,
        new_recommendation=new_rec,
    )
    state = ReviewState(decision_id=decision_id)
    state.override(event)

    console.print()
    console.print(Panel.fit("[bold]Override Recorded[/bold]"))
    console.print(f"\n  Decision: {decision_id}")
    console.print(f"  Actor: {actor}")
    if new_rec:
        console.print(f"  New recommendation: {new_rec}")
    console.print(f"  Reason: {reason}")
    console.print(f"  Hash: {event.audit_hash}\n")


@app.command(name="governance")
def governance_cmd(
    file: Path = typer.Argument(..., help="Path to decision result JSON"),
    rules_file: Optional[Path] = typer.Option(
        None, "--rules", help="Path to governance rules YAML",
    ),
) -> None:
    """Evaluate governance rules against a decision result."""
    import json

    import yaml

    from verdictcore.governance import GovernanceEngine
    from verdictcore.models.result import DecisionResult

    try:
        with open(file, "r") as f:
            data = json.load(f)
        result = DecisionResult(**data)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    rules = []
    if rules_file:
        with open(rules_file, "r", encoding="utf-8") as f:
            rules_data = yaml.safe_load(f)
        rules = rules_data.get("governance_rules", [])

    engine = GovernanceEngine.from_rules(rules)
    report = engine.evaluate(result)

    console.print()
    console.print(Panel.fit("[bold]Governance Report[/bold]"))
    console.print(f"\n  Decision: {report.decision_id}")
    console.print(f"  Risk level: {report.risk_level}")
    console.print(f"  Review required: {report.review_required}")
    console.print(f"  Approval required: {report.approval_required}")
    console.print(f"  Blocked: {report.blocked}")

    if report.reasons:
        console.print("\n[bold]Reasons:[/bold]")
        for r in report.reasons:
            console.print(f"  • {r}")

    if report.actions:
        console.print("\n[bold]Actions:[/bold]")
        for a in report.actions:
            console.print(f"  • [{a.action}] {a.message}")
    console.print()


@app.command(name="graph-run")
def graph_run(
    file: Path = typer.Argument(..., help="Path to graph YAML"),
) -> None:
    """Execute a decision DAG."""
    import yaml

    from verdictcore.dags import DAGExecutor, DecisionGraph

    try:
        with open(file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        graph = DecisionGraph(**data)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    executor = DAGExecutor()
    result = executor.execute(graph)

    console.print()
    console.print(Panel.fit("[bold]Decision Graph Result[/bold]"))
    console.print(f"\n  Graph: {result.graph_id}")
    console.print(f"  Status: {result.final_status.value}\n")

    console.print("[bold]Nodes:[/bold]")
    for nr in result.node_results:
        icon = "✓" if nr.status.value == "decided" else "✗"
        blocked = " [red](blocked upstream)[/red]" if nr.blocked_upstream else ""
        console.print(
            f"  {icon} {nr.node_name}: {nr.status.value}{blocked}"
        )

    final = result.final_result
    if final and final.selected_alternative_id:
        console.print(
            f"\n[bold]Final:[/bold] {final.selected_alternative_id}"
        )
    console.print()


@app.command(name="learning")
def learning_cmd(
    db: Path = typer.Option(
        "verdictcore.db", "--db", help="Registry database path",
    ),
    domain: Optional[str] = typer.Option(
        None, "--domain", help="Filter by domain",
    ),
) -> None:
    """Analyze outcomes and produce learning report."""
    from verdictcore.learning import OutcomeLearningAnalyzer
    from verdictcore.registry import SQLiteDecisionRegistry
    from verdictcore.registry.store import DecisionQuery

    registry = SQLiteDecisionRegistry(db)
    query = DecisionQuery(domain=domain) if domain else None
    results = registry.list_runs(query)

    all_outcomes = []
    for r in results:
        all_outcomes.extend(registry.get_outcomes(r.decision_id))
    registry.close()

    if not results or not all_outcomes:
        console.print("[yellow]Insufficient data for learning.[/yellow]")
        return

    analyzer = OutcomeLearningAnalyzer()
    report = analyzer.analyze(results, all_outcomes)

    console.print()
    console.print(Panel.fit("[bold]Outcome Learning Report[/bold]"))
    console.print(f"\n  Decisions analyzed: {report.decisions_analyzed}")

    if not report.patterns:
        console.print("  [green]No patterns detected.[/green]\n")
        return

    console.print("\n[bold]Patterns:[/bold]")
    for i, p in enumerate(report.patterns, 1):
        console.print(f"  {i}. [{p.pattern_type}] {p.target}")
        console.print(f"     {p.finding}")
        console.print(f"     → {p.recommendation}")
    console.print()


@app.command(name="simulate")
def simulate_cmd(
    file: Path = typer.Argument(..., help="Path to decision YAML"),
    iterations: int = typer.Option(5000, "--iterations", "-n", help="Iterations"),
    seed: int = typer.Option(42, "--seed", help="Random seed"),
) -> None:
    """Run Monte Carlo simulation on a decision."""
    import yaml

    from verdictcore.io import load_decision_yaml
    from verdictcore.simulation import SimulationEngine, SimulationVariable
    from verdictcore.simulation.variables import SimulationConfig

    try:
        decision_input = load_decision_yaml(str(file))
        with open(file, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    sim_data = raw.get("simulation", {})
    variables = [
        SimulationVariable(**v) for v in sim_data.get("variables", [])
    ]
    config = SimulationConfig(
        iterations=sim_data.get("iterations", iterations),
        seed=sim_data.get("seed", seed),
        variables=variables,
    )

    engine = SimulationEngine()
    result = engine.run(decision_input, config=config)

    console.print()
    console.print(Panel.fit("[bold]Simulation Result[/bold]"))
    console.print(f"\n  Decision: {result.decision_id}")
    console.print(f"  Iterations: {result.iterations}")
    console.print("\n[bold]Winner Distribution:[/bold]")
    for w in result.winner_distribution:
        console.print(f"  • {w.alternative_id}: {w.win_rate:.0%}")

    if result.selected_alternative:
        console.print(
            f"\n[bold]Recommended:[/bold] {result.selected_alternative}"
        )
        if result.selection_reason:
            console.print(f"  {result.selection_reason}")

    if result.interpretation:
        console.print("\n[bold]Interpretation:[/bold]")
        for note in result.interpretation:
            console.print(f"  {note}")
    console.print()


@app.command(name="stress-test")
def stress_test_cmd(
    file: Path = typer.Argument(..., help="Path to decision YAML"),
) -> None:
    """Run stress tests on a decision."""
    import yaml

    from verdictcore.io import load_decision_yaml
    from verdictcore.stress import StressScenario, StressTestEngine

    try:
        decision_input = load_decision_yaml(str(file))
        with open(file, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    stress_data = raw.get("stress_tests", [])
    if not stress_data:
        console.print("[yellow]No stress_tests defined in YAML.[/yellow]")
        raise typer.Exit(1)

    scenarios = [StressScenario(**s) for s in stress_data]
    engine = StressTestEngine()
    report = engine.run(decision_input, scenarios)

    console.print()
    console.print(Panel.fit("[bold]Stress Test Report[/bold]"))
    console.print(f"\n  Base winner: {report.base_winner}")
    console.print(f"  Vulnerability: {report.overall_vulnerability}\n")

    console.print("[bold]Results:[/bold]")
    for sr in report.stress_results:
        icon = "⚠" if sr.winner_changed else "✓"
        console.print(f"  {icon} {sr.scenario_name}")
        console.print(f"    Winner: {sr.winner} (changed: {sr.winner_changed})")
        console.print(f"    {sr.interpretation}")
    console.print()


@app.command(name="optimize")
def optimize_cmd(
    file: Path = typer.Argument(..., help="Path to decision YAML"),
) -> None:
    """Run Pareto frontier analysis."""
    import yaml

    from verdictcore.io import load_decision_yaml
    from verdictcore.optimization import ParetoAnalyzer
    from verdictcore.optimization.objectives import Objective

    try:
        decision_input = load_decision_yaml(str(file))
        with open(file, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    opt_data = raw.get("optimization", {})
    objectives_data = opt_data.get("objectives", [])

    if not objectives_data:
        objectives_data = [
            {"field": c.name, "direction": c.direction}
            for c in decision_input.criteria
        ]

    objectives = [Objective(**o) for o in objectives_data]
    analyzer = ParetoAnalyzer()
    report = analyzer.analyze(
        decision_input.decision_id,
        decision_input.alternatives,
        objectives,
    )

    console.print()
    console.print(Panel.fit("[bold]Pareto Analysis[/bold]"))

    console.print("\n[bold]Pareto Frontier:[/bold]")
    for p in report.pareto_frontier:
        strengths = ", ".join(p.strengths) if p.strengths else "—"
        weaknesses = ", ".join(p.weaknesses) if p.weaknesses else "—"
        console.print(f"  • {p.alternative_id}")
        console.print(f"    Strengths: {strengths}")
        console.print(f"    Weaknesses: {weaknesses}")

    if report.dominated_alternatives:
        console.print("\n[bold]Dominated:[/bold]")
        for d in report.dominated_alternatives:
            console.print(f"  • {d.alternative_id} — {d.reason}")

    if report.interpretation:
        console.print("\n[bold]Interpretation:[/bold]")
        for note in report.interpretation:
            console.print(f"  {note}")
    console.print()


@app.command(name="constraint-optimize")
def constraint_optimize_cmd(
    file: Path = typer.Argument(..., help="Path to decision YAML"),
) -> None:
    """Optimize constraint thresholds."""
    import yaml

    from verdictcore.io import load_decision_yaml
    from verdictcore.optimization import ConstraintOptimizer
    from verdictcore.optimization.constraint_optimizer import (
        ConstraintOptimizationInput,
    )

    try:
        decision_input = load_decision_yaml(str(file))
        with open(file, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    opt_data = raw.get("constraint_optimization", [])
    if not opt_data:
        console.print("[yellow]No constraint_optimization in YAML.[/yellow]")
        raise typer.Exit(1)

    optimizer = ConstraintOptimizer()
    for opt_item in opt_data:
        opt_input = ConstraintOptimizationInput(**opt_item)
        result = optimizer.optimize(decision_input, opt_input)

        console.print()
        console.print(
            Panel.fit(f"[bold]Constraint: {result.field} {result.operator}[/bold]")
        )
        for c in result.candidates:
            console.print(
                f"  {result.operator} {c.value}: blocked {c.blocked_rate:.0%}"
                f"  winner={c.winner}"
            )
        if result.recommended_threshold is not None:
            console.print(
                f"\n  [bold]Recommended:[/bold] {result.recommended_threshold}"
            )
            console.print(f"  {result.reason}")
    console.print()


@app.command(name="portfolio")
def portfolio_cmd(
    db: Path = typer.Option(
        "verdictcore.db", "--db", help="Registry database path",
    ),
    policy_file: Path = typer.Argument(..., help="Path to new policy YAML"),
    domain: Optional[str] = typer.Option(
        None, "--domain", help="Filter by domain",
    ),
) -> None:
    """Simulate policy impact across stored decisions."""
    import yaml

    from verdictcore.policies.model import DecisionPolicy
    from verdictcore.registry import SQLiteDecisionRegistry
    from verdictcore.registry.store import DecisionQuery

    try:
        with open(policy_file, "r", encoding="utf-8") as f:
            policy_data = yaml.safe_load(f)
        DecisionPolicy(**policy_data)  # validate
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    registry = SQLiteDecisionRegistry(db)
    query = DecisionQuery(domain=domain) if domain else None
    results = registry.list_runs(query)
    registry.close()

    if not results:
        console.print("[yellow]No decisions in registry.[/yellow]")
        return

    console.print(
        "[yellow]Portfolio simulation requires original DecisionInput"
        " objects which are not stored in registry.[/yellow]"
    )
    console.print(
        "Use the Python API: PortfolioSimulator.simulate_policy_impact()"
    )


@app.command(name="memory")
def memory_cmd(
    db: Path = typer.Option(
        "verdictcore.db", "--db", help="Registry database path",
    ),
    domain: Optional[str] = typer.Option(
        None, "--domain", help="Filter by domain",
    ),
) -> None:
    """Summarize decision memory."""
    from verdictcore.memory import DecisionMemory
    from verdictcore.registry import SQLiteDecisionRegistry
    from verdictcore.registry.store import DecisionQuery

    registry = SQLiteDecisionRegistry(db)
    query = DecisionQuery(domain=domain) if domain else None
    results = registry.list_runs(query)
    registry.close()

    if not results:
        console.print("[yellow]No decisions in registry.[/yellow]")
        return

    memory = DecisionMemory(results)
    summary = memory.summarize(domain=domain)

    console.print()
    console.print(Panel.fit("[bold]Decision Memory Summary[/bold]"))
    console.print(f"\n  Domain: {summary.domain}")
    console.print(f"  Decisions analyzed: {summary.decisions_analyzed}")
    console.print(f"  Override rate: {summary.override_rate:.0%}")
    console.print(f"  Fragile decision rate: {summary.fragile_decision_rate:.0%}")

    if summary.most_common_winners:
        console.print("\n[bold]Most common winners:[/bold]")
        for w in summary.most_common_winners[:5]:
            console.print(f"  • {w.get('alternative_id')}: {w.get('rate', 0):.0%}")

    if summary.status_distribution:
        console.print("\n[bold]Status distribution:[/bold]")
        for status, count in summary.status_distribution.items():
            console.print(f"  • {status}: {count}")
    console.print()


@app.command(name="patterns")
def patterns_cmd(
    db: Path = typer.Option(
        "verdictcore.db", "--db", help="Registry database path",
    ),
    domain: Optional[str] = typer.Option(
        None, "--domain", help="Filter by domain",
    ),
) -> None:
    """Discover patterns from decision history."""
    from verdictcore.patterns import PatternDiscovery
    from verdictcore.registry import SQLiteDecisionRegistry
    from verdictcore.registry.store import DecisionQuery

    registry = SQLiteDecisionRegistry(db)
    query = DecisionQuery(domain=domain) if domain else None
    results = registry.list_runs(query)
    registry.close()

    if not results:
        console.print("[yellow]No decisions in registry.[/yellow]")
        return

    discovery = PatternDiscovery()
    report = discovery.discover(results, domain=domain)

    console.print()
    console.print(Panel.fit("[bold]Pattern Discovery Report[/bold]"))
    console.print(f"\n  Domain: {report.domain}")
    console.print(f"  Decisions analyzed: {report.decisions_analyzed}")

    if not report.patterns:
        console.print("  [green]No patterns detected.[/green]\n")
        return

    console.print(f"\n[bold]Patterns ({len(report.patterns)}):[/bold]")
    for p in report.patterns:
        console.print(f"  • [{p.pattern_type}] {p.description}")
        if p.recommendation_hint:
            console.print(f"    → {p.recommendation_hint}")
    console.print()


@app.command(name="drift")
def drift_cmd(
    db: Path = typer.Option(
        "verdictcore.db", "--db", help="Registry database path",
    ),
    domain: Optional[str] = typer.Option(
        None, "--domain", help="Filter by domain",
    ),
) -> None:
    """Detect policy drift from decision outcomes."""
    from verdictcore.drift import DriftDetector
    from verdictcore.registry import SQLiteDecisionRegistry
    from verdictcore.registry.store import DecisionQuery

    registry = SQLiteDecisionRegistry(db)
    query = DecisionQuery(domain=domain) if domain else None
    results = registry.list_runs(query)
    outcomes = []
    for r in results:
        outcomes.extend(registry.get_outcomes(r.decision_id))
    registry.close()

    detector = DriftDetector()
    report = detector.detect(results, outcomes)

    console.print()
    console.print(Panel.fit("[bold]Drift Detection Report[/bold]"))
    console.print(f"\n  Overall drift: {report.overall_drift_level}")

    if not report.signals:
        console.print("  [green]No drift detected.[/green]\n")
        return

    console.print(f"\n[bold]Signals ({len(report.signals)}):[/bold]")
    for s in report.signals:
        console.print(f"  • [{s.severity}] {s.drift_type}: {s.description}")
        if s.recommended_action:
            console.print(f"    → {s.recommended_action}")
    console.print()


@app.command(name="adaptive")
def adaptive_cmd(
    db: Path = typer.Option(
        "verdictcore.db", "--db", help="Registry database path",
    ),
    domain: Optional[str] = typer.Option(
        None, "--domain", help="Filter by domain",
    ),
) -> None:
    """Generate adaptive policy suggestions."""
    from verdictcore.adaptive import AdaptiveSuggester
    from verdictcore.drift import DriftDetector
    from verdictcore.patterns import PatternDiscovery
    from verdictcore.registry import SQLiteDecisionRegistry
    from verdictcore.registry.store import DecisionQuery

    registry = SQLiteDecisionRegistry(db)
    query = DecisionQuery(domain=domain) if domain else None
    results = registry.list_runs(query)
    outcomes = []
    for r in results:
        outcomes.extend(registry.get_outcomes(r.decision_id))
    registry.close()

    if not results:
        console.print("[yellow]No decisions in registry.[/yellow]")
        return

    pattern_report = PatternDiscovery().discover(results, domain=domain)
    drift_report = DriftDetector().detect(results, outcomes)

    suggester = AdaptiveSuggester()
    report = suggester.suggest(
        pattern_report=pattern_report,
        drift_report=drift_report,
    )

    console.print()
    console.print(Panel.fit("[bold]Adaptive Policy Suggestions[/bold]"))

    if not report.suggestions:
        console.print("  [green]No suggestions at this time.[/green]\n")
        return

    console.print(f"\n[bold]Suggestions ({len(report.suggestions)}):[/bold]")
    for s in report.suggestions:
        console.print(f"  • [{s.suggestion_type}] {s.target}")
        console.print(f"    {s.reason}")
        console.print(f"    Confidence: {s.confidence:.0%} | Risk: {s.risk}")
        console.print(f"    Requires approval: {s.requires_human_approval}")
    console.print()


@app.command()
def version() -> None:
    """Show VerdictCore version."""
    console.print(f"VerdictCore v{__version__}")


def _print_result(result) -> None:

    status_color = {
        "decided": "green",
        "blocked": "red",
        "needs_review": "yellow",
        "insufficient_data": "yellow",
        "error": "red",
    }
    color = status_color.get(result.status.value, "white")

    console.print()
    console.print(Panel.fit(
        "[bold]VerdictCore DecisionRun[/bold]",
        subtitle=f"v{__version__}",
    ))
    console.print()

    console.print("[bold]Decision:[/bold]")
    console.print(f"  {result.question}")
    console.print()

    console.print(f"[bold]Status:[/bold] [{color}]{result.status.value}[/{color}]")
    console.print()

    if result.recommendation.selected_alternative_name:
        name = result.recommendation.selected_alternative_name
        console.print(f"[bold]Selected:[/bold] [green]{name}[/green]")
        console.print(f"[bold]Confidence:[/bold] {result.recommendation.confidence:.2f}")
        console.print()

    # Rankings table
    table = Table(title="Rankings")
    table.add_column("Rank", justify="center")
    table.add_column("Alternative")
    table.add_column("Score", justify="right")
    table.add_column("Status")

    for r in result.rankings:
        rank_str = str(r.rank) if r.rank else "—"
        status_str = "[red]BLOCKED[/red]" if r.blocked else "[green]✓[/green]"
        if r.warnings:
            status_str = f"[yellow]⚠ {r.warnings[0]}[/yellow]"
        table.add_row(rank_str, r.name, f"{r.total_score:.1f}", status_str)

    console.print(table)
    console.print()

    # Blocked constraints
    failed = [cr for cr in result.constraint_results if not cr.passed]
    if failed:
        console.print("[bold]Constraint Violations:[/bold]")
        for cr in failed:
            console.print(
                f"  [red]•[/red] {cr.alternative_name}:"
                f" {cr.field} {cr.operator} {cr.required_value} "
                f"(actual: {cr.actual_value}) → {cr.action}"
            )
        console.print()

    # Explanation
    _print_explanation(result)


def _print_explanation(result) -> None:
    console.print("[bold]Why Selected:[/bold]")
    console.print(f"  {result.explanation.why_selected}")
    console.print()

    if result.explanation.top_drivers:
        console.print("[bold]Top Drivers:[/bold]")
        for d in result.explanation.top_drivers:
            console.print(f"  • {d.criterion}: +{d.impact:.2f}")
        console.print()

    if result.explanation.why_not:
        console.print("[bold]Why Not:[/bold]")
        for wn in result.explanation.why_not:
            console.print(f"  • {wn.alternative_name}: {wn.reason}")
        console.print()

    if result.explanation.sensitivity:
        sens = result.explanation.sensitivity
        console.print(
            f"[bold]Decision Stability:[/bold]"
            f" {sens.level} ({sens.decision_stability_score:.2f})"
        )
        if sens.sensitive_to:
            console.print(f"  Sensitive to: {', '.join(sens.sensitive_to)}")
        console.print()

    # Audit
    console.print("[bold]Audit:[/bold]")
    console.print(f"  input_hash:   {result.audit.input_hash}")
    console.print(f"  ruleset_hash: {result.audit.ruleset_hash}")
    console.print(f"  output_hash:  {result.audit.output_hash}")
    console.print()


if __name__ == "__main__":
    app()
