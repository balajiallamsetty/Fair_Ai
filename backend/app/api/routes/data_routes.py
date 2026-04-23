"""API routes for data ingestion module."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.app.core.database import get_database
from backend.app.core.security import get_current_user, get_current_user_with_access
from backend.app.schemas.dataset_schema import DatasetListResponse, DatasetResponse, DatasetUploadForm
from backend.app.schemas.user_schema import UserPublic
from backend.app.services.data_service import get_dataset_by_id, ingest_dataset, list_datasets
from backend.app.utils.helpers import document_to_schema


router = APIRouter(prefix="/data", tags=["data"])


@router.post("/datasets/upload", response_model=DatasetResponse)
async def upload_dataset(
	name: str = Form(...),
	description: str | None = Form(None),
	target_column: str = Form(...),
	sensitive_columns: str = Form(..., description="Comma-separated sensitive columns."),
	feature_columns: str | None = Form(None, description="Optional comma-separated feature columns."),
	file: UploadFile = File(...),
	current_user: UserPublic = Depends(get_current_user),
	database=Depends(get_database),
) -> DatasetResponse:
	"""Upload and ingest a dataset CSV."""

	payload = DatasetUploadForm(
		name=name,
		description=description,
		target_column=target_column,
		sensitive_columns=[item.strip() for item in sensitive_columns.split(",") if item.strip()],
		feature_columns=[item.strip() for item in feature_columns.split(",") if item.strip()] if feature_columns else None,
	)
	return await ingest_dataset(
		database=database,
		owner_id=current_user.id,
		payload=payload,
		upload=file,
	)


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def fetch_dataset(
	dataset_id: str,
	current_user: UserPublic = Depends(get_current_user_with_access("datasets")),
	database=Depends(get_database),
) -> DatasetResponse:
	"""Get a single dataset by identifier."""

	dataset = await get_dataset_by_id(database, dataset_id)
	return document_to_schema(dataset, DatasetResponse)


@router.get("/datasets", response_model=DatasetListResponse)
async def fetch_datasets(
	mine: bool = False,
	current_user: UserPublic = Depends(get_current_user),
	database=Depends(get_database),
) -> DatasetListResponse:
	"""List available datasets."""

	owner_id = current_user.id if mine else None
	datasets = await list_datasets(database, owner_id=owner_id)
	return DatasetListResponse(
		datasets=[document_to_schema(item, DatasetResponse) for item in datasets],
		total=len(datasets),
	)


@router.get("/datasets/{dataset_id}/profile")
async def fetch_dataset_profile(
	dataset_id: str,
	current_user: UserPublic = Depends(get_current_user_with_access("datasets")),
	database=Depends(get_database),
) -> dict:
	"""Get dataset profile snapshot."""

	dataset = await get_dataset_by_id(database, dataset_id)
	return {
		"id": str(dataset["_id"]),
		"profile": dataset["profile"],
		"created_at": dataset["created_at"],
	}

