"""Missing data handling policies."""

from __future__ import annotations

from enum import Enum


class MissingPolicy(str, Enum):

    PENALIZE = "penalize"
    IGNORE = "ignore"
    NEEDS_REVIEW = "needs_review"
