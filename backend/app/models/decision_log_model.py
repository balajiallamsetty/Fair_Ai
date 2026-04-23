"""Persistence models for prediction decisions and review queues."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DecisionLogDocument(BaseModel):
    """MongoDB representation of an inference decision log."""

    id: str | None = Field(default=None, alias="_id")
    model_id: str
    dataset_id: str | None = None
    input_payload: dict[str, Any]
    prediction: int
    probability: float
    sensitive_snapshot: dict[str, Any]
    fairness_snapshot: dict[str, Any]
    flags: list[str]
    requires_review: bool = False
    created_at: datetime

    model_config = {"populate_by_name": True}
