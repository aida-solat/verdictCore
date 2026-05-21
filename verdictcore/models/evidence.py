"""Evidence model for decision values."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

SourceType = Literal[
    "official_document",
    "vendor_statement",
    "third_party_report",
    "manual_entry",
    "llm_extracted",
    "structured_import",
    "api",
    "unknown",
]

ExtractionMethod = Literal[
    "manual",
    "structured_import",
    "llm_extraction",
    "api",
    "unknown",
]


class Evidence(BaseModel):

    id: str
    alternative_id: str | None = None
    field: str | None = None
    source: str
    source_type: SourceType = "unknown"
    claim: str
    value: Any | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reliability: float | None = Field(default=None, ge=0.0, le=1.0)
    freshness_days: int | None = None
    extraction_method: ExtractionMethod = "unknown"
    metadata: dict[str, Any] = {}
