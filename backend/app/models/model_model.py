"""Persistence model definitions for trained models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModelDocument(BaseModel):
    """MongoDB representation of a trained model artifact."""

    id: str | None = Field(default=None, alias="_id")
    name: str
    dataset_id: str
    owner_id: str
    algorithm: str
    target_column: str
    sensitive_columns: list[str]
    feature_columns: list[str]
    artifact_path: str
    preprocessing_artifact_path: str | None = None
    training_summary: dict[str, Any]
    fairness_metrics: dict[str, Any]
    mitigation_results: dict[str, Any] | None = None
    explainability: dict[str, Any] | None = None
    model_card: dict[str, Any]
    status: str = "ready"
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}
