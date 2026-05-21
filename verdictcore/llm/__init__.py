"""Optional LLM integration for VerdictCore.

BOUNDARY RULE: LLMs can explain, summarize, and extract evidence.
They CANNOT override deterministic decisions, modify scores, or bypass constraints.
"""

from verdictcore.llm.boundary import LLMBoundary

__all__ = ["LLMBoundary"]
