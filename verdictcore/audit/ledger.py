"""Audit event chain."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from verdictcore.models.audit import AuditEvent


class AuditLedger:

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event_type: str, details: dict[str, str] | None = None) -> AuditEvent:
        prev_hash = self.events[-1].hash if self.events else None

        event_data = {
            "event_type": event_type,
            "prev_hash": prev_hash,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        event_hash = "sha256:" + hashlib.sha256(
            json.dumps(event_data, sort_keys=True).encode()
        ).hexdigest()

        event = AuditEvent(
            event_type=event_type,
            hash=event_hash,
            prev_hash=prev_hash,
            details=details or {},
        )
        self.events.append(event)
        return event

    def verify_chain(self) -> bool:
        for i, event in enumerate(self.events):
            if i == 0:
                if event.prev_hash is not None:
                    return False
            else:
                if event.prev_hash != self.events[i - 1].hash:
                    return False
        return True
