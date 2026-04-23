"""Bias mitigation engine service."""

from __future__ import annotations

import pickle
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, status
from sklearn.model_selection import train_test_split

from backend.app.core.config import get_settings
from backend.app.services.fairness_service import compute_fairness_metrics
from backend.app.services.model_service import get_model_by_id, load_model_artifact
from backend.app.utils.helpers import create_audit_log, object_id_str, utc_now


def _build_weights(series: pd.Series) -> list[float]:
	"""Build inverse-frequency weights for reweighting strategy."""

	counts = Counter(series.astype(str))
	total = sum(counts.values())
	return [float(total / (len(counts) * counts[str(value)])) for value in series]


def _upsample_by_group(frame: pd.DataFrame, group_column: str) -> pd.DataFrame:
	"""Upsample minority groups to match the max group count."""

	grouped = [subset for _, subset in frame.groupby(frame[group_column].astype(str))]
	if not grouped:
		return frame
	max_count = max(len(subset) for subset in grouped)
	sampled: list[pd.DataFrame] = []
	for subset in grouped:
		sampled.append(subset.sample(n=max_count, replace=len(subset) < max_count, random_state=42))
	return pd.concat(sampled, axis=0).sample(frac=1.0, random_state=42).reset_index(drop=True)


def _save_updated_artifact(payload: dict[str, Any]) -> str:
	"""Persist mitigation-updated model artifact."""

	settings = get_settings()
	path = settings.model_artifacts_dir / f"model_mitigated_{uuid4().hex}.pkl"
	with path.open("wb") as file_pointer:
		pickle.dump(payload, file_pointer)
	return str(path)


	def _predict_class_probability(pipeline, frame: pd.DataFrame) -> tuple[int, float]:
	    """Return the predicted class and its probability."""

	    prediction = int(pipeline.predict(frame)[0])
	    probabilities = pipeline.predict_proba(frame)[0]
	    class_index = int(list(pipeline.classes_).index(prediction))
	    return prediction, float(probabilities[class_index])


async def apply_mitigation_strategy(
	*,
	database,
	model_id: str,
	strategy: str,
	actor_id: str,
	actor_role: str,
) -> dict[str, Any]:
	"""Apply mitigation strategy and store before/after fairness comparison."""

	normalized_strategy = strategy.strip().lower()
	if normalized_strategy not in {"reweighting", "resampling"}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supported strategies: reweighting, resampling.")

	model = await get_model_by_id(database, model_id)
	dataset = await database["datasets"].find_one({"_id": object_id_str(model["dataset_id"], as_object_id=True)})
	if dataset is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model dataset not found.")

	frame = pd.read_csv(dataset["file_path"])
	artifact = load_model_artifact(model["artifact_path"])
	pipeline = artifact["pipeline"]
	feature_columns = artifact["feature_columns"]
	target_column = artifact["target_column"]
	sensitive_columns = artifact.get("sensitive_columns") or []
	primary_sensitive = sensitive_columns[0] if sensitive_columns else None
	if primary_sensitive is None or primary_sensitive not in frame.columns:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No primary sensitive column for mitigation.")

	X = frame[feature_columns]
	y = pd.to_numeric(frame[target_column], errors="coerce").fillna(0).astype(int)

	X_train, X_test, y_train, y_test = train_test_split(
		X,
		y,
		test_size=0.2,
		random_state=42,
		stratify=y if y.nunique() > 1 else None,
	)
	sensitive_test = frame.loc[X_test.index, primary_sensitive].astype(str)
	baseline_pred = pd.Series(pipeline.predict(X_test))
	before_metrics = compute_fairness_metrics(
		y_true=y_test.reset_index(drop=True),
		y_pred=baseline_pred.reset_index(drop=True),
		sensitive_series=sensitive_test.reset_index(drop=True),
	)

	if normalized_strategy == "reweighting":
		weights = _build_weights(frame.loc[X_train.index, primary_sensitive])
		pipeline.fit(X_train, y_train, classifier__sample_weight=weights)
	else:
		train_frame = frame.loc[X_train.index, feature_columns + [target_column, primary_sensitive]].copy()
		resampled = _upsample_by_group(train_frame, primary_sensitive)
		pipeline.fit(resampled[feature_columns], pd.to_numeric(resampled[target_column], errors="coerce").fillna(0).astype(int))

	mitigated_pred = pd.Series(pipeline.predict(X_test))
	after_metrics = compute_fairness_metrics(
		y_true=y_test.reset_index(drop=True),
		y_pred=mitigated_pred.reset_index(drop=True),
		sensitive_series=sensitive_test.reset_index(drop=True),
	)

	artifact["pipeline"] = pipeline
	new_artifact_path = _save_updated_artifact(artifact)
	mitigation_results = {
		"strategy": normalized_strategy,
		"before": before_metrics,
		"after": after_metrics,
		"applied_at": utc_now(),
	}
	await database["models"].update_one(
		{"_id": model["_id"]},
		{
			"$set": {
				"artifact_path": str(Path(new_artifact_path)),
				"mitigation_results": mitigation_results,
				"updated_at": utc_now(),
			}
		},
	)
	await create_audit_log(
		database,
		actor_id=actor_id,
		actor_role=actor_role,
		action="model.mitigation_applied",
		entity_type="model",
		entity_id=str(model["_id"]),
		details={"strategy": normalized_strategy},
	)
	return mitigation_results


