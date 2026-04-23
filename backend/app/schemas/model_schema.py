"""Pydantic schemas for model training, mitigation, inference, and explainability."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from enum import Enum

from pydantic import BaseModel, ConfigDict, StrictBool, StrictFloat, StrictInt, StrictStr


class MitigationStrategy(str, Enum):
    """Supported mitigation strategies."""

    reweighting = "reweighting"
    resampling = "resampling"


class ModelTrainRequest(BaseModel):
    """Request schema for model training."""

    dataset_id: str
    name: str
    test_size: float = 0.2
    random_state: int = 42


class ModelResponse(BaseModel):
    """Model response schema."""

    id: str
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
    status: str
    created_at: datetime
    updated_at: datetime


class MitigationRequest(BaseModel):
    """Request schema for post-training mitigation."""

    strategy: MitigationStrategy


class PredictionRequest(BaseModel):
    """Request schema for live inference."""

    features: dict[str, StrictStr | StrictInt | StrictFloat | StrictBool]
    sensitive_attributes: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")


class PredictionResponse(BaseModel):
    """Prediction response schema."""

    model_id: str
    prediction: int
    probability: float
    fairness_snapshot: dict[str, Any]
    flags: list[str]
    requires_review: bool
    decision_log_id: str


class CounterfactualRequest(BaseModel):
    """Request schema for counterfactual analysis."""

    base_features: dict[str, Any]
    candidate_changes: list[dict[str, Any]]


class ExplainabilityResponse(BaseModel):
    """Explainability response schema."""

    feature_importance: list[dict[str, Any]]
    baseline_prediction: dict[str, Any]
    counterfactuals: list[dict[str, Any]]
