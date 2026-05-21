"""Evidence extraction interface."""

from __future__ import annotations

from pydantic import BaseModel


class ExtractedEvidence(BaseModel):

    field: str
    value: float | int | str | None = None
    claim: str
    source_snippet: str
    confidence: float


def extract_evidence_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "evidence_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {
                            "type": "string",
                            "description": "Which criterion this relates to",
                        },
                        "value": {
                            "description": "Numeric or categorical value",
                        },
                        "claim": {
                            "type": "string",
                            "description": "The factual claim being made",
                        },
                        "source_snippet": {
                            "type": "string",
                            "description": "Relevant text snippet",
                        },
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["field", "claim", "source_snippet", "confidence"],
                },
            }
        },
        "required": ["evidence_items"],
    }
