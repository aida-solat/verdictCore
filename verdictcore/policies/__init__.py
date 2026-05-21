"""Policy versioning, diffing, and recommendations."""

from verdictcore.policies.diff import PolicyDiff, diff_policies
from verdictcore.policies.model import DecisionPolicy

__all__ = ["DecisionPolicy", "PolicyDiff", "diff_policies"]
