"""Explainability service for feature importance and counterfactual checks."""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import HTTPException, status

from backend.app.schemas.model_schema import CounterfactualRequest, ExplainabilityResponse
from backend.app.services.model_service import get_model_by_id, load_model_artifact
from backend.app.utils.helpers import create_audit_log, utc_now


def _predicted_class_probability(pipeline, frame: pd.DataFrame) -> tuple[int, float]:
	"""Return the predicted class and the probability assigned to it."""

	prediction = int(pipeline.predict(frame)[0])
	probabilities = pipeline.predict_proba(frame)[0]
	class_index = int(list(pipeline.classes_).index(prediction))
	return prediction, float(probabilities[class_index])


def _extract_feature_importance(artifact: dict[str, Any]) -> list[dict[str, Any]]:
	"""Extract feature importance from logistic regression coefficients."""

	pipeline = artifact["pipeline"]
	preprocessor = pipeline.named_steps["preprocessor"]
	classifier = pipeline.named_steps["classifier"]

	if not hasattr(classifier, "coef_"):
		return []
	if not hasattr(preprocessor, "get_feature_names_out"):
		return []

	feature_names = list(preprocessor.get_feature_names_out())
	coefficients = classifier.coef_[0]
	ranked = sorted(
		zip(feature_names, coefficients),
		key=lambda item: abs(float(item[1])),
		reverse=True,
	)
	return [
		{"feature": feature, "coefficient": float(coef), "absolute_importance": abs(float(coef))}
		for feature, coef in ranked
	]


async def explain_model_predictions(
	*,
	database,
	model_id: str,
	payload: CounterfactualRequest,
	actor_id: str,
	actor_role: str,
) -> ExplainabilityResponse:
	"""Generate feature importance and evaluate counterfactual outcomes."""

	model = await get_model_by_id(database, model_id)
	artifact = load_model_artifact(model["artifact_path"])
	pipeline = artifact["pipeline"]
	feature_columns = artifact["feature_columns"]

	missing_base = [column for column in feature_columns if column not in payload.base_features]
	if missing_base:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing base features: {missing_base}")

	baseline_row = {column: payload.base_features[column] for column in feature_columns}
	baseline_frame = pd.DataFrame([baseline_row])
	baseline_prediction, baseline_probability = _predicted_class_probability(pipeline, baseline_frame)

	counterfactuals: list[dict[str, Any]] = []
	for change in payload.candidate_changes:
		candidate = {**baseline_row, **change}
		candidate_frame = pd.DataFrame([candidate])
		prediction, probability = _predicted_class_probability(pipeline, candidate_frame)
		counterfactuals.append(
			{
				"changes": change,
				"prediction": prediction,
				"probability": probability,
				"prediction_changed": prediction != baseline_prediction,
			}
		)

	feature_importance = _extract_feature_importance(artifact)[:20]
	explainability_payload = {
		"last_generated_at": utc_now(),
		"top_feature_importance": feature_importance[:10],
		"counterfactual_count": len(counterfactuals),
	}
	await database["models"].update_one(
		{"_id": model["_id"]},
		{"$set": {"explainability": explainability_payload, "updated_at": utc_now()}},
	)
	await create_audit_log(
		database,
		actor_id=actor_id,
		actor_role=actor_role,
		action="model.explainability_generated",
		entity_type="model",
		entity_id=str(model["_id"]),
		details={"counterfactuals": len(counterfactuals)},
	)
	return ExplainabilityResponse(
		feature_importance=feature_importance,
		baseline_prediction={"prediction": baseline_prediction, "probability": baseline_probability},
		counterfactuals=counterfactuals,
	)

