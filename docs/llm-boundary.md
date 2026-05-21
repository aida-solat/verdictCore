# LLM Boundary

## Core Principle

> **VerdictCore separates decision logic from language generation.**

The deterministic engine produces the decision. The LLM (optionally) produces the narrative.

## Allowed LLM Uses

| Use Case                   | Description                                                   |
| -------------------------- | ------------------------------------------------------------- |
| **Narrative generation**   | Summarize a DecisionResult in natural language                |
| **Evidence extraction**    | Parse unstructured documents into structured Evidence objects |
| **Missing info detection** | Suggest questions to fill data gaps                           |
| **Report enhancement**     | Add context to Markdown/PDF reports                           |

## Disallowed LLM Uses

| Violation                          | Why                    |
| ---------------------------------- | ---------------------- |
| Modify final scores                | Breaks determinism     |
| Override constraints               | Breaks governance      |
| Select winners                     | Breaks reproducibility |
| Generate unaudited recommendations | Breaks audit trail     |
| Bypass decision status             | Breaks compliance      |

## Enforcement

The `LLMBoundary` class ensures integrity:

```python
from verdictcore.llm import LLMBoundary

result = engine.run(decision_input)
boundary = LLMBoundary(result)

# Get read-only context for the LLM
context = boundary.get_context_for_narrative()

# After LLM interaction, verify nothing was modified
assert boundary.verify_integrity()
```

## Architecture

```
DecisionInput → Deciwa → DecisionResult (frozen)
                                        ↓
                                  LLMBoundary (read-only view)
                                        ↓
                                  Narrative / Summary
```

The LLM never touches the engine. It only reads the output.

## Future (v0.5)

Full LLM integration with:

- OpenAI structured outputs
- Anthropic tool use
- Local model support (Ollama, vLLM)
- Evidence extraction pipeline
- Automatic narrative generation
