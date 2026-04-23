"""Model training module service."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, status
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

from backend.app.core.config import get_settings
from backend.app.schemas.model_schema import ModelResponse, ModelTrainRequest
from backend.app.services.data_service import get_dataset_by_id
from backend.app.services.fairness_service import compute_fairness_metrics
from backend.app.utils.helpers import create_audit_log, document_to_schema, object_id_str, utc_now


def _build_pipeline(frame: pd.DataFrame, feature_columns: list[str]) -> Pipeline:
	"""Build an sklearn pipeline for mixed feature types."""

	feature_frame = frame[feature_columns].copy()
	categorical_features = list(feature_frame.select_dtypes(include=["object", "category", "bool", "datetime", "datetimetz"]).columns)
	numeric_features = [column for column in feature_columns if column not in categorical_features]

	transformer = ColumnTransformer(
		transformers=[
			("num", StandardScaler(), numeric_features),
			("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
		],
		remainder="drop",
	)
	return Pipeline(
		steps=[
			("preprocessor", transformer),
			("classifier", LogisticRegression(max_iter=1000, solver="lbfgs")),
		]
	)


def _serialize_classification_report(report: dict[str, Any]) -> dict[str, Any]:
	"""Convert numpy scalar values to plain Python types."""

	output: dict[str, Any] = {}
	for key, value in report.items():
		if isinstance(value, dict):
			output[key] = {
				nested_key: float(nested_value) if isinstance(nested_value, (int, float)) else nested_value
				for nested_key, nested_value in value.items()
			}
		elif isinstance(value, (int, float)):
			output[key] = float(value)
		else:
			output[key] = value
	return output


def _save_model_artifact(payload: dict[str, Any]) -> str:
	"""Persist model artifact payload to disk."""

	settings = get_settings()
	settings.model_artifacts_dir.mkdir(parents=True, exist_ok=True)
	path = settings.model_artifacts_dir / f"model_{uuid4().hex}.pkl"
	with path.open("wb") as file_pointer:
		pickle.dump(payload, file_pointer)
	return str(path)


def load_model_artifact(path: str) -> dict[str, Any]:
	"""Load model artifact payload from disk."""

	artifact_path = Path(path)
	if not artifact_path.exists():
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model artifact not found on disk.")
	with artifact_path.open("rb") as file_pointer:
		return pickle.load(file_pointer)


async def train_logistic_model(
	*,
	database,
	owner_id: str,
	owner_role: str,
	payload: ModelTrainRequest,
) -> ModelResponse:
	"""Train and persist a logistic regression model for a dataset."""

	dataset = await get_dataset_by_id(database, payload.dataset_id)
	frame = pd.read_csv(dataset["file_path"])

	target_column = dataset["target_column"]
	feature_columns = dataset["feature_columns"]
	sensitive_columns = dataset["sensitive_columns"]

	if target_column not in frame.columns:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target column missing in dataset.")
	if not feature_columns:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No feature columns available.")

	X = frame[feature_columns].copy()
	target_series = frame[target_column].astype(str).fillna("missing")
	label_encoder = LabelEncoder()
	y_encoded = label_encoder.fit_transform(target_series)
	if len(label_encoder.classes_) != 2:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only binary classification targets are supported.")
	y = pd.Series(y_encoded, index=frame.index)
	class_counts = y.value_counts()
	test_sample_count = max(1, round(len(y) * payload.test_size))
	can_stratify = len(class_counts) > 1 and class_counts.min() >= 2 and test_sample_count >= len(class_counts)

	X_train, X_test, y_train, y_test = train_test_split(
		X,
		y,
		test_size=payload.test_size,
		random_state=payload.random_state,
		stratify=y if can_stratify else None,
	)

	pipeline = _build_pipeline(frame, feature_columns)
	pipeline.fit(X_train, y_train)
	y_pred = pd.Series(pipeline.predict(X_test))

	primary_sensitive = sensitive_columns[0] if sensitive_columns else None
	sensitive_series = (
		frame.loc[X_test.index, primary_sensitive].astype(str)
		if primary_sensitive and primary_sensitive in frame.columns
		else pd.Series(["unknown"] * len(X_test), index=X_test.index)
	)
	fairness_metrics = compute_fairness_metrics(y_true=y_test.reset_index(drop=True), y_pred=y_pred, sensitive_series=sensitive_series.reset_index(drop=True))

	training_summary = {
		"algorithm": "logistic_regression",
		"test_size": payload.test_size,
		"accuracy": float(accuracy_score(y_test, y_pred)),
		"classification_report": _serialize_classification_report(
			classification_report(y_test, y_pred, output_dict=True, zero_division=0)
		),
		"records_used": int(len(frame)),
	}

	artifact_payload = {
		"pipeline": pipeline,
		"feature_columns": feature_columns,
		"target_column": target_column,
		"sensitive_columns": sensitive_columns,
		"label_encoder": label_encoder,
		"dataset_id": str(dataset["_id"]),
	}
	artifact_path = _save_model_artifact(artifact_payload)

	now = utc_now()
	model_document = {
		"name": payload.name,
		"dataset_id": str(dataset["_id"]),
		"owner_id": owner_id,
		"algorithm": "logistic_regression",
		"target_column": target_column,
		"sensitive_columns": sensitive_columns,
		"feature_columns": feature_columns,
		"artifact_path": artifact_path,
		"preprocessing_artifact_path": None,
		"training_summary": training_summary,
		"fairness_metrics": fairness_metrics,
		"mitigation_results": None,
		"explainability": None,
		"model_card": {
			"model_name": payload.name,
			"version": "1.0.0",
			"owner": owner_id,
			"intended_use": "Binary decision support",
			"limitations": ["Sensitive to data drift", "Requires periodic fairness review"],
			"ethical_considerations": ["Monitor disparate impact", "Use human review for flagged decisions"],
		},
		"status": "ready",
		"created_at": now,
		"updated_at": now,
	}
	result = await database["models"].insert_one(model_document)
	inserted = await database["models"].find_one({"_id": result.inserted_id})
	assert inserted is not None

	await create_audit_log(
		database,
		actor_id=owner_id,
		actor_role=owner_role,
		action="model.trained",
		entity_type="model",
		entity_id=str(result.inserted_id),
		details={"dataset_id": str(dataset["_id"]), "algorithm": "logistic_regression"},
	)
	return document_to_schema(inserted, ModelResponse)


async def get_model_by_id(database, model_id: str) -> dict[str, Any]:
	"""Return a model document by identifier."""

	model = await database["models"].find_one({"_id": object_id_str(model_id, as_object_id=True)})
	if model is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
	return model


async def list_models(database, *, owner_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
	"""List model documents optionally filtered by owner."""

	query = {"owner_id": owner_id} if owner_id else {}
	cursor = database["models"].find(query).sort("created_at", -1).limit(limit)
	return [item async for item in cursor]

