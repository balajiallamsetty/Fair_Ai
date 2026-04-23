"""API routes for governance module and authentication."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.core.database import get_database
from backend.app.core.security import (
	authenticate_user,
	create_access_token,
	get_current_user,
	get_password_hash,
	require_roles,
)
from backend.app.schemas.user_schema import TokenResponse, UserCreate, UserLogin, UserPublic
from backend.app.services.monitoring_service import generate_governance_report, resolve_review_item
from backend.app.utils.helpers import create_audit_log, document_to_schema, serialize_document, utc_now


router = APIRouter(prefix="/governance", tags=["governance"])


@router.post("/auth/register", response_model=UserPublic)
async def register_user(payload: UserCreate, database=Depends(get_database)) -> UserPublic:
	"""Register a platform user."""

	existing = await database["users"].find_one({"email": payload.email})
	if existing is not None:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")

	now = utc_now()
	document = {
		"email": payload.email,
		"full_name": payload.full_name,
		"hashed_password": get_password_hash(payload.password),
		"role": payload.role,
		"is_active": True,
		"created_at": now,
		"updated_at": now,
	}
	result = await database["users"].insert_one(document)
	inserted = await database["users"].find_one({"_id": result.inserted_id})
	assert inserted is not None

	await create_audit_log(
		database,
		actor_id=str(result.inserted_id),
		actor_role=payload.role,
		action="user.registered",
		entity_type="user",
		entity_id=str(result.inserted_id),
		details={"email": payload.email},
	)
	return document_to_schema(inserted, UserPublic)


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: UserLogin, database=Depends(get_database)) -> TokenResponse:
	"""Authenticate a user and issue JWT."""

	user = await authenticate_user(database, payload.email, payload.password)
	if user is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email/password.")

	access_token = create_access_token(subject=str(user["_id"]), role=user["role"])
	return TokenResponse(access_token=access_token, user=document_to_schema(user, UserPublic))


@router.get("/report")
async def get_governance_report(
	dataset_id: str | None = None,
	model_id: str | None = None,
	page: int = Query(1, ge=1),
	page_size: int = Query(50, ge=1, le=200),
	current_user: UserPublic = Depends(require_roles("admin", "auditor")),
	database=Depends(get_database),
) -> dict:
	"""Generate governance report with alerts, audit logs, and review queue."""

	return await generate_governance_report(
		database=database,
		actor_id=current_user.id,
		actor_role=current_user.role,
		dataset_id=dataset_id,
		model_id=model_id,
		page=page,
		page_size=page_size,
	)


@router.get("/model-card/{model_id}")
async def get_model_card(
	model_id: str,
	_: UserPublic = Depends(get_current_user),
	database=Depends(get_database),
) -> dict:
	"""Return model card details."""

	from backend.app.utils.helpers import object_id_str

	model = await database["models"].find_one({"_id": object_id_str(model_id, as_object_id=True)})
	if model is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
	return {"model_id": model_id, "model_card": serialize_document(model.get("model_card", {}))}


@router.get("/review-queue")
async def list_review_queue(
	status_filter: str = "pending",
	_: UserPublic = Depends(require_roles("admin", "auditor")),
	database=Depends(get_database),
) -> dict:
	"""List human-in-the-loop review queue items."""

	cursor = database["review_queue"].find({"status": status_filter}).sort("created_at", -1).limit(100)
	items = [serialize_document(item) async for item in cursor]
	return {"items": items, "total": len(items)}


@router.post("/review-queue/{review_id}/resolve")
async def resolve_review(
	review_id: str,
	decision: Literal["approved", "rejected"],
	current_user: UserPublic = Depends(require_roles("admin", "auditor")),
	database=Depends(get_database),
) -> dict:
	"""Resolve a review queue item and close related alert if present."""

	result = await resolve_review_item(
		database=database,
		review_id=review_id,
		decision=decision,
		actor_id=current_user.id,
		actor_role=current_user.role,
	)
	alert_id = result.get("alert_id")
	if alert_id:
		from backend.app.utils.helpers import object_id_str

		await database["monitoring_alerts"].update_one(
			{"_id": object_id_str(alert_id, as_object_id=True)},
			{"$set": {"status": "closed", "updated_at": utc_now()}},
		)
	return result

