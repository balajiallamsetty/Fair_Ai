"""Persistence model definitions for datasets."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DatasetDocument(BaseModel):
    """MongoDB representation of an uploaded dataset."""

    id: str | None = Field(default=None, alias="_id")
    name: str
    description: str | None = None
    owner_id: str
    file_path: str
    schema_definition: dict[str, str]
    target_column: str
    sensitive_columns: list[str]
    feature_columns: list[str]
    profile: dict[str, Any]
    preprocessing: dict[str, Any]
    bias_report: dict[str, Any] | None = None
    sample_preview: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}
