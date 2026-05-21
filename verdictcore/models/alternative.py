"""Decision alternative (candidate option)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Alternative(BaseModel):

    id: str
    name: str
    values: dict[str, float | int | str | None]
    metadata: dict[str, Any] = {}
