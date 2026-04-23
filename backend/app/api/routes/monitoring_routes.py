"""API routes for monitoring module."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.core.database import get_database
from backend.app.core.security import get_current_user, require_roles
from backend.app.schemas.model_schema import PredictionRequest, PredictionResponse
from backend.app.schemas.user_schema import UserPublic
from backend.app.services.monitoring_service import list_monitoring_alerts, predict_and_monitor


router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.post("/models/{model_id}/predict", response_model=PredictionResponse)
async def predict(
	model_id: str,
	payload: PredictionRequest,
	current_user: UserPublic = Depends(require_roles("admin", "auditor", "user")),
	database=Depends(get_database),
) -> PredictionResponse:
	"""Run online prediction and monitoring checks."""

	return await predict_and_monitor(
		database=database,
		model_id=model_id,
		payload=payload,
		actor_id=current_user.id,
		actor_role=current_user.role,
	)


@router.get("/alerts")
async def get_alerts(
	model_id: str | None = None,
	status: str | None = None,
	_: UserPublic = Depends(get_current_user),
	database=Depends(get_database),
) -> dict:
	"""List monitoring alerts."""

	alerts = await list_monitoring_alerts(database, model_id=model_id, status_filter=status)
	return {"alerts": alerts, "total": len(alerts)}

