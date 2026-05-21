"""Scoring strategies for VerdictCore."""

from verdictcore.scoring.normalization import normalize_values
from verdictcore.scoring.ranking import rank_alternatives
from verdictcore.scoring.weighted import WeightedScorer

__all__ = [
    "WeightedScorer",
    "normalize_values",
    "rank_alternatives",
]
