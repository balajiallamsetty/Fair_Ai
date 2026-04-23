"""API routes for bias detection engine."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.database import get_database
from backend.app.core.security import get_current_user, get_current_user_with_access, require_roles
from backend.app.schemas.bias_schema import BiasAnalysisResponse
from backend.app.schemas.user_schema import UserPublic
from backend.app.services.bias_service import run_bias_analysis


router = APIRouter(prefix="/bias", tags=["bias"])


@router.post("/datasets/{dataset_id}/analyze", response_model=BiasAnalysisResponse)
async def analyze_dataset_bias(
	dataset_id: str,
	current_user: UserPublic = Depends(require_roles("admin", "auditor", "user")),
	database=Depends(get_database),
) -> BiasAnalysisResponse:
	"""Run full bias analysis for a dataset."""

	return await run_bias_analysis(
		database=database,
		dataset_id=dataset_id,
		actor_id=current_user.id,
		actor_role=current_user.role,
	)


@router.get("/datasets/{dataset_id}/report")
async def get_bias_report(
	dataset_id: str,
	current_user: UserPublic = Depends(get_current_user_with_access("datasets")),
	database=Depends(get_database),
) -> dict:
	"""Get the latest stored bias report from dataset document."""

	from backend.app.utils.helpers import object_id_str, serialize_document

	dataset = await database["datasets"].find_one({"_id": object_id_str(dataset_id, as_object_id=True)})
	if dataset is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
	if not dataset.get("bias_report"):
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bias report not found for dataset.")
	return {"dataset_id": dataset_id, "bias_report": serialize_document(dataset["bias_report"])}

