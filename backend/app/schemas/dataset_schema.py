"""Pydantic schemas for dataset ingestion and retrieval."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DatasetUploadForm(BaseModel):
    """Structured dataset upload metadata."""

    name: str
    description: str | None = None
    target_column: str
    sensitive_columns: list[str]
    feature_columns: list[str] | None = None
    schema_definition: dict[str, str] | None = None


class DatasetResponse(BaseModel):
    """Dataset response schema."""

    id: str
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


class DatasetListResponse(BaseModel):
    """Dataset list response schema."""

    datasets: list[DatasetResponse]
    total: int


class DatasetProfileResponse(BaseModel):
    """Dataset profile-only response."""

    dataset_id: str = Field(alias="id")
    profile: dict[str, Any]
    created_at: datetime

    model_config = {"populate_by_name": True}
