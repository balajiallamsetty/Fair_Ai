"""API routes for model lifecycle modules."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.database import get_database
from backend.app.core.security import get_current_user, get_current_user_with_access, require_roles
from backend.app.schemas.model_schema import (
	CounterfactualRequest,
	ExplainabilityResponse,
	MitigationRequest,
	ModelResponse,
	ModelTrainRequest,
)
from backend.app.schemas.user_schema import UserPublic
from backend.app.services.explainability_service import explain_model_predictions
from backend.app.services.mitigation_service import apply_mitigation_strategy
from backend.app.services.model_service import get_model_by_id, list_models, train_logistic_model
from backend.app.utils.helpers import document_to_schema


router = APIRouter(prefix="/models", tags=["models"])


@router.post("/train", response_model=ModelResponse)
async def train_model(
	payload: ModelTrainRequest,
	current_user: UserPublic = Depends(require_roles("admin", "auditor", "user")),
	database=Depends(get_database),
) -> ModelResponse:
	"""Train logistic regression model and persist metadata."""

	return await train_logistic_model(
		database=database,
		owner_id=current_user.id,
		owner_role=current_user.role,
		payload=payload,
	)


@router.get("/{model_id}", response_model=ModelResponse)
async def fetch_model(
	model_id: str,
	current_user: UserPublic = Depends(get_current_user_with_access("models")),
	database=Depends(get_database),
) -> ModelResponse:
	"""Get model details by id."""

	model = await get_model_by_id(database, model_id)
	return document_to_schema(model, ModelResponse)


@router.get("", response_model=list[ModelResponse])
async def fetch_models(
	mine: bool = False,
	current_user: UserPublic = Depends(get_current_user),
	database=Depends(get_database),
) -> list[ModelResponse]:
	"""List trained models."""

	owner_id = current_user.id if mine or current_user.role != "admin" else None
	models = await list_models(database, owner_id=owner_id)
	return [document_to_schema(item, ModelResponse) for item in models]


@router.post("/{model_id}/mitigate")
async def mitigate_model(
	model_id: str,
	payload: MitigationRequest,
	current_user: UserPublic = Depends(require_roles("admin", "auditor")),
	database=Depends(get_database),
) -> dict:
	"""Apply mitigation strategy and return comparison report."""

	result = await apply_mitigation_strategy(
		database=database,
		model_id=model_id,
		strategy=payload.strategy,
		actor_id=current_user.id,
		actor_role=current_user.role,
	)
	return {"model_id": model_id, "mitigation": result}


@router.post("/{model_id}/explain", response_model=ExplainabilityResponse)
async def explain_model(
	model_id: str,
	payload: CounterfactualRequest,
	current_user: UserPublic = Depends(require_roles("admin", "auditor", "user")),
	database=Depends(get_database),
) -> ExplainabilityResponse:
	"""Generate explainability and counterfactual output."""

	return await explain_model_predictions(
		database=database,
		model_id=model_id,
		payload=payload,
		actor_id=current_user.id,
		actor_role=current_user.role,
	)

