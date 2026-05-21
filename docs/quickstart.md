# Quickstart

## Installation

```bash
pip install verdictcore
```

Or for development:

```bash
git clone https://github.com/your-username/verdictcore.git
cd verdictcore
pip install -e ".[dev]"
```

## Your First Decision (CLI)

```bash
verdict run examples/ai_model_selection/decision.yaml
```

This will:

1. Load the decision YAML
2. Evaluate constraints (block/warn/escalate)
3. Score alternatives using weighted criteria
4. Rank eligible alternatives
5. Generate explanations
6. Run sensitivity analysis
7. Print the result with full audit trail

## Your First Decision (Python)

```python
from verdictcore import Deciwa
from verdictcore.io import load_decision_yaml

# Load from YAML
decision_input = load_decision_yaml("examples/ai_model_selection/decision.yaml")

# Run the engine
engine = Deciwa()
result = engine.run(decision_input)

# Access the result
print(result.status)                              # "decided"
print(result.recommendation.selected_alternative_name)  # "Claude Sonnet"
print(result.explanation.why_selected)            # Natural language explanation
print(result.why_not("model_a"))                  # Why Model A wasn't selected
print(result.explanation.sensitivity.level)       # "moderately_stable"
```

## Export Results

```python
from verdictcore.io import export_json, export_markdown

# Canonical JSON
export_json(result, "output.json")

# Markdown report
export_markdown(result, "report.md")
```

## Validate Without Running

```bash
verdict validate decision.yaml
```

## Next Steps

- Read [Decision Object](decision-object.md) to understand the data model
- Read [LLM Boundary](llm-boundary.md) to understand what LLMs can and cannot do
- Read [Audit Model](audit-model.md) for compliance and reproducibility
- Check [examples/](../examples/) for ready-to-run decisions
