"""Audit event model."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):

    event_type: str
    actor: str = "system"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hash: str
    prev_hash: str | None = None
    details: dict[str, str] = {}
