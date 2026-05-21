"""Review and override event models."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

ReviewStatus = Literal[
    "not_required",
    "required",
    "in_review",
    "approved",
    "rejected",
    "overridden",
    "escalated",
]


class ReviewRule(BaseModel):

    id: str
    condition: str
    action: Literal["require_review", "require_approval", "escalate"]
    message: str


class OverrideEvent(BaseModel):

    decision_id: str
    actor_id: str
    actor_role: str | None = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    previous_recommendation: str | None = None
    new_recommendation: str | None = None
    reason: str
    evidence_refs: list[str] = []
    audit_hash: str | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.audit_hash is None:
            payload = json.dumps({
                "decision_id": self.decision_id,
                "actor_id": self.actor_id,
                "timestamp": self.timestamp.isoformat(),
                "reason": self.reason,
                "new_recommendation": self.new_recommendation,
            }, sort_keys=True)
            self.audit_hash = hashlib.sha256(
                payload.encode(),
            ).hexdigest()[:16]


class ReviewState(BaseModel):

    decision_id: str
    status: ReviewStatus = "not_required"
    required_by: str | None = None
    reason: str | None = None
    overrides: list[OverrideEvent] = []
    comments: list[str] = []
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def require_review(self, reason: str, required_by: str | None = None) -> None:
        self.status = "required"
        self.reason = reason
        self.required_by = required_by
        self._touch()

    def approve(self, actor_id: str) -> None:
        self.status = "approved"
        self.comments.append(f"Approved by {actor_id}")
        self._touch()

    def reject(self, actor_id: str, reason: str) -> None:
        self.status = "rejected"
        self.comments.append(f"Rejected by {actor_id}: {reason}")
        self._touch()

    def override(self, event: OverrideEvent) -> None:
        self.status = "overridden"
        self.overrides.append(event)
        self._touch()

    def escalate(self, reason: str) -> None:
        self.status = "escalated"
        self.reason = reason
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
