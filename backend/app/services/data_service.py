"""Data ingestion module service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException, UploadFile, status

from backend.app.core.config import get_settings
from backend.app.schemas.dataset_schema import DatasetResponse, DatasetUploadForm
from backend.app.utils.helpers import (
	build_dataset_profile,
	clean_column_names,
	create_audit_log,
	document_to_schema,
	infer_schema,
	object_id_str,
	persist_dataframe,
	read_csv_upload,
	utc_now,
)


def _apply_missing_value_strategy(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
	"""Fill missing values using deterministic column-aware strategies."""

	frame = dataframe.copy()
	strategy: dict[str, Any] = {"numeric": "median", "categorical": "mode", "applied": {}}
	for column in frame.columns:
		if frame[column].isna().sum() == 0:
			continue
		if pd.api.types.is_numeric_dtype(frame[column]):
			fill_value = float(frame[column].median()) if not frame[column].dropna().empty else 0.0
		else:
			mode_values = frame[column].mode(dropna=True)
			fill_value = str(mode_values.iloc[0]) if not mode_values.empty else "unknown"
		frame[column] = frame[column].fillna(fill_value)
		strategy["applied"][column] = fill_value
	return frame, strategy


def _resolve_feature_columns(frame: pd.DataFrame, payload: DatasetUploadForm) -> list[str]:
	"""Resolve feature columns from payload or defaults."""

	if payload.feature_columns:
		return payload.feature_columns
	excluded = {payload.target_column, *payload.sensitive_columns}
	return [column for column in frame.columns if column not in excluded]


def _mask_sensitive_preview(frame: pd.DataFrame, sensitive_columns: list[str]) -> list[dict[str, Any]]:
	"""Return a masked preview that avoids exposing raw sensitive values."""

	preview = frame.head(10).copy()
	for column in sensitive_columns:
		if column in preview.columns:
			preview[column] = preview[column].astype(str).map(lambda _: "***masked***")
	return preview.to_dict(orient="records")


async def ingest_dataset(
	*,
	database,
	owner_id: str,
	payload: DatasetUploadForm,
	upload: UploadFile,
) -> DatasetResponse:
	"""Upload, validate, preprocess, and persist a dataset metadata record."""

	settings = get_settings()
	raw_frame = clean_column_names(await read_csv_upload(upload))
	payload = DatasetUploadForm.model_validate(
		{
			**payload.model_dump(),
			"target_column": payload.target_column.strip().lower().replace(" ", "_"),
			"sensitive_columns": [item.strip().lower().replace(" ", "_") for item in payload.sensitive_columns],
			"feature_columns": [item.strip().lower().replace(" ", "_") for item in payload.feature_columns]
			if payload.feature_columns
			else None,
		}
	)

	if payload.target_column not in raw_frame.columns:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Target column '{payload.target_column}' not found.",
		)

	missing_sensitive = [column for column in payload.sensitive_columns if column not in raw_frame.columns]
	if missing_sensitive:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Sensitive columns not found: {missing_sensitive}",
		)

	feature_columns = _resolve_feature_columns(raw_frame, payload)
	missing_features = [column for column in feature_columns if column not in raw_frame.columns]
	if missing_features:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Feature columns not found: {missing_features}",
		)

	clean_frame, preprocessing = _apply_missing_value_strategy(raw_frame)
	profile = build_dataset_profile(raw_frame)
	file_path = persist_dataframe(clean_frame, settings.dataset_artifacts_dir, "dataset")
	now = utc_now()

	document = {
		"name": payload.name,
		"description": payload.description,
		"owner_id": owner_id,
		"file_path": str(Path(file_path)),
		"schema_definition": payload.schema_definition or infer_schema(clean_frame),
		"target_column": payload.target_column,
		"sensitive_columns": payload.sensitive_columns,
		"feature_columns": feature_columns,
		"profile": profile,
		"preprocessing": preprocessing,
		"bias_report": None,
		"sample_preview": _mask_sensitive_preview(clean_frame, payload.sensitive_columns),
		"created_at": now,
		"updated_at": now,
	}
	result = await database["datasets"].insert_one(document)
	inserted = await database["datasets"].find_one({"_id": result.inserted_id})
	assert inserted is not None

	await create_audit_log(
		database,
		actor_id=owner_id,
		actor_role="user",
		action="dataset.uploaded",
		entity_type="dataset",
		entity_id=str(result.inserted_id),
		details={"name": payload.name, "target_column": payload.target_column},
	)
	return document_to_schema(inserted, DatasetResponse)


async def get_dataset_by_id(database, dataset_id: str) -> dict[str, Any]:
	"""Return a dataset document by identifier."""

	dataset = await database["datasets"].find_one({"_id": object_id_str(dataset_id, as_object_id=True)})
	if dataset is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
	return dataset


async def list_datasets(database, *, owner_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
	"""List datasets optionally filtered by owner."""

	query = {"owner_id": owner_id} if owner_id else {}
	cursor = database["datasets"].find(query).sort("created_at", -1).limit(limit)
	return [item async for item in cursor]

