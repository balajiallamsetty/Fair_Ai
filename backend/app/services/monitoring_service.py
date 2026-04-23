"""Real-time monitoring and governance service."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from pymongo import ReturnDocument

from backend.app.core.config import get_settings
from backend.app.schemas.model_schema import PredictionRequest, PredictionResponse
from backend.app.services.fairness_service import compute_live_fairness_snapshot
from backend.app.services.model_service import get_model_by_id, load_model_artifact
from backend.app.utils.helpers import create_audit_log, object_id_str, serialize_document, utc_now


_LIVE_WINDOW_CACHE: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=200))
_REPORT_CACHE: dict[str, tuple[datetime, dict[str, Any]]] = {}
_REPORT_CACHE_TTL_SECONDS = 60


def _predicted_class_probability(pipeline, frame: pd.DataFrame) -> tuple[int, float]:
	"""Return the predicted class and its class-specific probability."""

	prediction = int(pipeline.predict(frame)[0])
	probabilities = pipeline.predict_proba(frame)[0]
	class_index = int(list(pipeline.classes_).index(prediction))
	return prediction, float(probabilities[class_index])


async def predict_and_monitor(
	*,
	database,
	model_id: str,
	payload: PredictionRequest,
	actor_id: str,
	actor_role: str,
) -> PredictionResponse:
	"""Execute prediction, persist decision logs, and run live fairness checks."""

	settings = get_settings()
	model = await get_model_by_id(database, model_id)
	artifact = load_model_artifact(model["artifact_path"])
	pipeline = artifact["pipeline"]
	feature_columns = artifact["feature_columns"]
	primary_sensitive = model["sensitive_columns"][0] if model.get("sensitive_columns") else "sensitive_group"

	missing = [column for column in feature_columns if column not in payload.features]
	if missing:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Missing required feature fields: {missing}",
		)

	row = {column: payload.features.get(column) for column in feature_columns}
	frame = pd.DataFrame([row])
	prediction, probability = _predicted_class_probability(pipeline, frame)

	cache = _LIVE_WINDOW_CACHE[str(model["_id"])]
	if len(cache) < max(0, settings.fairness_monitor_window - 1):
		recent_logs = [
			item
			async for item in database["decision_logs"]
			.find({"model_id": str(model["_id"])})
			.sort("created_at", -1)
			.limit(settings.fairness_monitor_window - 1)
		]
		cache.clear()
		for item in reversed(recent_logs):
			cache.append(item)
	recent_logs = list(cache)
	current_sensitive_snapshot = payload.sensitive_attributes or {}
	window_logs = list(recent_logs)
	window_logs.append(
		{
			"prediction": prediction,
			"sensitive_snapshot": current_sensitive_snapshot,
		}
	)
	fairness_snapshot = compute_live_fairness_snapshot(logs=window_logs, sensitive_key=primary_sensitive)

	flags: list[str] = []
	if fairness_snapshot["parity_gap"] > settings.prediction_bias_threshold:
		flags.append("live_parity_gap_exceeded")
	if probability < 0.55:
		flags.append("low_confidence_prediction")

	requires_review = bool(flags)
	now = utc_now()
	decision_document = {
		"model_id": str(model["_id"]),
		"dataset_id": model.get("dataset_id"),
		"input_payload": payload.features,
		"prediction": prediction,
		"probability": probability,
		"sensitive_snapshot": current_sensitive_snapshot,
		"fairness_snapshot": fairness_snapshot,
		"flags": flags,
		"requires_review": requires_review,
		"created_at": now,
	}
	decision_result = await database["decision_logs"].insert_one(decision_document)

	if requires_review:
		alert_document = {
			"model_id": str(model["_id"]),
			"alert_type": "fairness" if "live_parity_gap_exceeded" in flags else "confidence",
			"severity": "high" if "live_parity_gap_exceeded" in flags else "medium",
			"message": "Live fairness threshold exceeded." if "live_parity_gap_exceeded" in flags else "Prediction confidence below threshold.",
			"triggered_by": {
				"decision_log_id": str(decision_result.inserted_id),
				"parity_gap": fairness_snapshot["parity_gap"],
				"probability": probability,
			},
			"status": "open",
			"created_at": now,
		}
		alert_result = await database["monitoring_alerts"].insert_one(alert_document)
		await database["review_queue"].insert_one(
			{
				"decision_log_id": str(decision_result.inserted_id),
				"model_id": str(model["_id"]),
				"reason": flags,
				"status": "pending",
				"assigned_to": None,
				"created_at": now,
				"updated_at": now,
				"alert_id": str(alert_result.inserted_id),
			}
		)

	cache.append(
		{
			"prediction": prediction,
			"sensitive_snapshot": current_sensitive_snapshot,
		}
	)

	await create_audit_log(
		database,
		actor_id=actor_id,
		actor_role=actor_role,
		action="prediction.executed",
		entity_type="model",
		entity_id=str(model["_id"]),
		details={"flags": flags, "requires_review": requires_review},
	)
	return PredictionResponse(
		model_id=str(model["_id"]),
		prediction=prediction,
		probability=probability,
		fairness_snapshot=fairness_snapshot,
		flags=flags,
		requires_review=requires_review,
		decision_log_id=str(decision_result.inserted_id),
	)


async def list_monitoring_alerts(database, *, model_id: str | None = None, status_filter: str | None = None) -> list[dict[str, Any]]:
	"""Return monitoring alerts for a model or globally."""

	query: dict[str, Any] = {}
	if model_id:
		query["model_id"] = model_id
	if status_filter:
		query["status"] = status_filter
	cursor = database["monitoring_alerts"].find(query).sort("created_at", -1).limit(100)
	return [serialize_document(item) async for item in cursor]


async def generate_governance_report(
	*,
	database,
	actor_id: str,
	actor_role: str,
	dataset_id: str | None = None,
	model_id: str | None = None,
	page: int = 1,
	page_size: int = 50,
) -> dict[str, Any]:
	"""Generate governance report with audit, alerts, reviews, and model card details."""

	cache_key = f"{dataset_id or 'all'}:{model_id or 'all'}"
	cached = _REPORT_CACHE.get(cache_key)
	now = utc_now()
	if cached is not None:
		cached_at, payload = cached
		if (now - cached_at).total_seconds() <= _REPORT_CACHE_TTL_SECONDS:
			return payload

	dataset = None
	model = None
	if dataset_id:
		dataset = await database["datasets"].find_one({"_id": object_id_str(dataset_id, as_object_id=True)})
	if model_id:
		model = await database["models"].find_one({"_id": object_id_str(model_id, as_object_id=True)})

	alerts_query = {"model_id": model_id} if model_id else {}
	review_query = {"model_id": model_id} if model_id else {}
	skip = (page - 1) * page_size

	alerts = [
		serialize_document(item)
		async for item in database["monitoring_alerts"].find(alerts_query).sort("created_at", -1).skip(skip).limit(page_size)
	]
	reviews = [
		serialize_document(item)
		async for item in database["review_queue"].find(review_query).sort("created_at", -1).skip(skip).limit(page_size)
	]
	audit_logs = [
		serialize_document(item)
		async for item in database["audit_logs"].find({}).sort("created_at", -1).skip(skip).limit(page_size)
	]

	report = {
		"generated_at": now,
		"dataset": serialize_document(dataset) if dataset else None,
		"model": serialize_document(model) if model else None,
		"alerts": alerts,
		"open_reviews": [item for item in reviews if item.get("status") == "pending"],
		"audit_logs": audit_logs,
	}
	_REPORT_CACHE[cache_key] = (now, report)
	await create_audit_log(
		database,
		actor_id=actor_id,
		actor_role=actor_role,
		action="governance.report_generated",
		entity_type="report",
		entity_id=model_id or dataset_id or "global",
		details={"dataset_id": dataset_id, "model_id": model_id},
	)
	return report


async def resolve_review_item(
	*,
	database,
	review_id: str,
	decision: str,
	actor_id: str,
	actor_role: str,
) -> dict[str, Any]:
	"""Mark a review queue item as approved or rejected."""

	if decision not in {"approved", "rejected"}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decision must be approved or rejected.")

	result = await database["review_queue"].find_one_and_update(
		{"_id": object_id_str(review_id, as_object_id=True)},
		{
			"$set": {
				"status": decision,
				"reviewed_by": actor_id,
				"reviewed_by_role": actor_role,
				"updated_at": utc_now(),
			}
		},
		return_document=ReturnDocument.AFTER,
	)
	if result is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review queue item not found.")

	await create_audit_log(
		database,
		actor_id=actor_id,
		actor_role=actor_role,
		action="governance.review_resolved",
		entity_type="review_queue",
		entity_id=review_id,
		details={"decision": decision},
	)
	return serialize_document(result)

