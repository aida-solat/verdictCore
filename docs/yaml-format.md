# YAML Decision Format

## Structure

```yaml
decision:
  id: <string>              # Optional, auto-generated if absent
  domain: <string>          # Category (e.g., "ai_model_selection")
  question: <string>        # The question being decided
  policy_version: <string>  # Version of the decision policy
  missing_policy: <string>  # "penalize" | "ignore" | "needs_review"

criteria:
  - name: <string>
    weight: <float>         # 0.0 to 1.0 (all weights should sum to 1.0)
    direction: <string>     # "maximize" or "minimize"
    description: <string>   # Optional
    required: <bool>        # Optional, default true
    scale: <string>         # Optional: "numeric" | "percentage" | "score"

constraints:
  - field: <string>         # Which criterion/field to check
    operator: <string>      # ">", ">=", "<", "<=", "==", "!=", "in", "not_in"
    value: <any>            # The threshold value
    action: <string>        # "block" | "warn" | "escalate"
    message: <string>       # Optional, human-readable explanation

alternatives:
  - id: <string>
    name: <string>
    values:
      <criterion_name>: <number or string>
    metadata: {}            # Optional key-value pairs

evidence:                   # Optional
  - id: <string>
    alternative_id: <string>
    field: <string>
    source: <string>
    claim: <string>
    value: <any>
    confidence: <float>     # 0.0 to 1.0
    reliability: <float>    # 0.0 to 1.0

metadata: {}                # Optional decision-level metadata
```

## Example

```yaml
decision:
  id: cloud_001
  domain: cloud_vendor_selection
  question: Which cloud provider?
  policy_version: v1

criteria:
  - name: cost
    weight: 0.3
    direction: minimize
  - name: reliability
    weight: 0.4
    direction: maximize
  - name: security
    weight: 0.3
    direction: maximize

constraints:
  - field: security
    operator: ">="
    value: 80
    action: block
    message: Security must be >= 80

alternatives:
  - id: aws
    name: AWS
    values:
      cost: 72
      reliability: 95
      security: 92
  - id: gcp
    name: GCP
    values:
      cost: 68
      reliability: 93
      security: 88
```

## Validation

```bash
verdict validate decision.yaml
```

## Tips

- Weights should sum to 1.0 (a warning is shown if they don't)
- Use descriptive constraint messages — they appear in explanations
- Keep criterion names consistent between `criteria` and `alternatives.values`
- Missing values are handled according to `missing_policy`
