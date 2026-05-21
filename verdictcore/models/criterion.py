"""Decision criterion definition."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Criterion(BaseModel):

    name: str
    weight: float = Field(ge=0.0, le=1.0)
    direction: Literal["maximize", "minimize"]
    description: str | None = None
    required: bool = True
    scale: Literal["numeric", "percentage", "score"] = "numeric"
