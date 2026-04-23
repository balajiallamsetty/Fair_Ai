"""Persistence models for bias and monitoring artifacts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BiasReportDocument(BaseModel):
    """Embedded bias report representation."""

    generated_at: datetime
    bias_score: float
    group_analysis: dict[str, Any]
    distribution_comparison: dict[str, Any]
    proxy_detection: dict[str, Any]
    intersectional_analysis: dict[str, Any]
    recommendations: list[str]


class MonitoringAlertDocument(BaseModel):
    """MongoDB representation of a live monitoring alert."""

    id: str | None = Field(default=None, alias="_id")
    model_id: str
    alert_type: str
    severity: str
    message: str
    triggered_by: dict[str, Any]
    status: str = "open"
    created_at: datetime

    model_config = {"populate_by_name": True}
