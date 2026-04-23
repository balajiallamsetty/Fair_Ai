"""Pydantic schemas for bias analysis and governance reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BiasAnalysisResponse(BaseModel):
    """Bias analysis response schema."""

    dataset_id: str
    generated_at: datetime
    bias_score: float
    group_analysis: dict[str, Any]
    distribution_comparison: dict[str, Any]
    proxy_detection: dict[str, Any]
    intersectional_analysis: dict[str, Any]
    recommendations: list[str]


class MonitoringAlertResponse(BaseModel):
    """Monitoring alert response schema."""

    id: str
    model_id: str
    alert_type: str
    severity: str
    message: str
    triggered_by: dict[str, Any]
    status: str
    created_at: datetime


class GovernanceReportResponse(BaseModel):
    """Governance report response schema."""

    generated_at: datetime
    dataset: dict[str, Any] | None = None
    model: dict[str, Any] | None = None
    alerts: list[dict[str, Any]]
    open_reviews: list[dict[str, Any]]
    audit_logs: list[dict[str, Any]]
