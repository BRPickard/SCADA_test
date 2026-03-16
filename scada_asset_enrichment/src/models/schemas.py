"""Pydantic schema models used by enrichment providers."""
from __future__ import annotations

from pydantic import BaseModel


class EnrichedField(BaseModel):
    field_name: str
    value: str | int | float | bool | None
    source_provider: str
    source_reference: str
    confidence: float
    extraction_notes: str
