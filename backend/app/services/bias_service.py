"""Bias detection engine service."""

from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException, status

from backend.app.schemas.bias_schema import BiasAnalysisResponse
from backend.app.services.data_service import get_dataset_by_id
from backend.app.utils.helpers import create_audit_log, utc_now
from backend.app.utils.metrics import bias_score_from_components


def _distribution_distance(frame: pd.DataFrame, target_column: str, sensitive_column: str) -> dict[str, float]:
	"""Estimate pairwise distribution distance by normalized histogram L1 distance."""

	output: dict[str, float] = {}
	groups = frame[sensitive_column].astype(str).unique().tolist()
	for left, right in combinations(groups, 2):
		left_values = pd.to_numeric(frame.loc[frame[sensitive_column].astype(str) == left, target_column], errors="coerce").dropna()
		right_values = pd.to_numeric(frame.loc[frame[sensitive_column].astype(str) == right, target_column], errors="coerce").dropna()
		if left_values.empty or right_values.empty:
			output[f"{left}_vs_{right}"] = 0.0
			continue
		hist_l, bins = np.histogram(left_values, bins=min(10, max(3, left_values.nunique())), density=True)
		hist_r, _ = np.histogram(right_values, bins=bins, density=True)
		output[f"{left}_vs_{right}"] = float(np.abs(hist_l - hist_r).sum() / 2)
	return output


def _proxy_detection(frame: pd.DataFrame, sensitive_columns: list[str]) -> dict[str, Any]:
	"""Find high-correlation proxy features against sensitive attributes."""

	encoded = frame.copy()
	for column in encoded.columns:
		if not pd.api.types.is_numeric_dtype(encoded[column]):
			encoded[column] = pd.factorize(encoded[column].astype(str))[0]
	correlation = encoded.corr(numeric_only=True).fillna(0)
	potential_proxies: list[dict[str, Any]] = []
	for sensitive in sensitive_columns:
		if sensitive not in correlation.columns:
			continue
		for feature, value in correlation[sensitive].to_dict().items():
			if feature == sensitive:
				continue
			score = abs(float(value))
			if score >= 0.6:
				potential_proxies.append(
					{
						"sensitive_feature": sensitive,
						"proxy_feature": feature,
						"correlation": float(value),
					}
				)
	return {
		"potential_proxies": potential_proxies,
		"correlation_matrix": correlation.round(4).to_dict(),
	}


async def run_bias_analysis(*, database, dataset_id: str, actor_id: str, actor_role: str) -> BiasAnalysisResponse:
	"""Run complete dataset bias analysis and persist report in dataset document."""

	dataset = await get_dataset_by_id(database, dataset_id)
	frame = pd.read_csv(dataset["file_path"])
	target_column = dataset["target_column"]
	sensitive_columns = dataset["sensitive_columns"]

	if target_column not in frame.columns:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target column missing in dataset file.")

	group_analysis: dict[str, Any] = {}
	distribution_comparison: dict[str, Any] = {}
	group_components: list[float] = []

	for sensitive in sensitive_columns:
		if sensitive not in frame.columns:
			continue
		grouped = frame.groupby(frame[sensitive].astype(str))[target_column].mean().fillna(0)
		values = grouped.to_dict()
		group_analysis[sensitive] = {"group_target_means": {key: float(value) for key, value in values.items()}}
		if len(values) > 1:
			group_components.append(float(max(values.values()) - min(values.values())))
		distribution_comparison[sensitive] = _distribution_distance(frame, target_column, sensitive)

	intersectional_analysis: dict[str, Any] = {}
	if len(sensitive_columns) >= 2:
		for left, right in combinations(sensitive_columns, 2):
			if left not in frame.columns or right not in frame.columns:
				continue
			key = f"{left}__{right}"
			subset = frame.groupby([frame[left].astype(str), frame[right].astype(str)])[target_column].mean().fillna(0)
			mapping = {f"{idx[0]}|{idx[1]}": float(value) for idx, value in subset.to_dict().items()}
			intersectional_analysis[key] = mapping
			if len(mapping) > 1:
				intersectional_components = list(mapping.values())
				group_components.append(float(max(intersectional_components) - min(intersectional_components)))

	proxy_detection = _proxy_detection(frame, sensitive_columns)
	if proxy_detection["potential_proxies"]:
		group_components.append(min(1.0, 0.1 * len(proxy_detection["potential_proxies"])))

	bias_score = bias_score_from_components(group_components)
	recommendations = [
		"Review sensitive feature distributions and sampling coverage.",
		"Evaluate proxy features with high correlations for leakage risk.",
		"Run mitigation module if bias score exceeds governance threshold.",
	]
	report = {
		"generated_at": utc_now(),
		"bias_score": float(bias_score),
		"group_analysis": group_analysis,
		"distribution_comparison": distribution_comparison,
		"proxy_detection": proxy_detection,
		"intersectional_analysis": intersectional_analysis,
		"recommendations": recommendations,
	}
	await database["datasets"].update_one(
		{"_id": dataset["_id"]},
		{"$set": {"bias_report": report, "updated_at": utc_now()}},
	)
	await create_audit_log(
		database,
		actor_id=actor_id,
		actor_role=actor_role,
		action="dataset.bias_analyzed",
		entity_type="dataset",
		entity_id=str(dataset["_id"]),
		details={"bias_score": float(bias_score)},
	)
	return BiasAnalysisResponse(dataset_id=str(dataset["_id"]), **report)

