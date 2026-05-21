"""VerdictCore — Deterministic decisions. Explainable tradeoffs. Audit-ready outputs."""

from verdictcore.engine import Deciwa
from verdictcore.models.alternative import Alternative
from verdictcore.models.constraint import Constraint
from verdictcore.models.criterion import Criterion
from verdictcore.models.decision import DecisionInput
from verdictcore.models.evidence import Evidence
from verdictcore.models.result import DecisionResult
from verdictcore.version import __version__

__all__ = [
    "Deciwa",
    "DecisionInput",
    "Alternative",
    "Criterion",
    "Constraint",
    "Evidence",
    "DecisionResult",
    "__version__",
]
