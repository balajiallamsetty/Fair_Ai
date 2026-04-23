"""Fairness metrics engine service."""

from __future__ import annotations

from typing import Any

import pandas as pd

from backend.app.utils.metrics import demographic_parity, disparate_impact, equal_opportunity


def compute_fairness_metrics(
	*,
	y_true: pd.Series,
	y_pred: pd.Series,
	sensitive_series: pd.Series,
) -> dict[str, Any]:
	"""Compute the platform fairness metrics for a model run."""

	dp = demographic_parity(y_pred=y_pred, sensitive=sensitive_series)
	eo = equal_opportunity(y_true=y_true, y_pred=y_pred, sensitive=sensitive_series)
	di = disparate_impact(y_pred=y_pred, sensitive=sensitive_series)
	return {
		"demographic_parity": dp,
		"equal_opportunity": eo,
		"disparate_impact": di,
		"flags": {
			"parity_difference_high": abs(dp.get("difference", 0.0)) > 0.2,
			"equal_opportunity_gap_high": abs(eo.get("difference", 0.0)) > 0.2,
			"disparate_impact_outside_80pct_rule": di.get("ratio", 1.0) < 0.8,
		},
	}


def compute_live_fairness_snapshot(
	*,
	logs: list[dict[str, Any]],
	sensitive_key: str,
) -> dict[str, Any]:
	"""Compute fairness snapshot over recent decision logs."""

	if not logs:
		return {"window_size": 0, "group_positive_rates": {}, "parity_gap": 0.0}

	frame = pd.DataFrame(
		{
			"prediction": [item.get("prediction", 0) for item in logs],
			"group": [
				str((item.get("sensitive_snapshot") or {}).get(sensitive_key, "unknown"))
				for item in logs
			],
		}
	)
	rates = frame.groupby("group")["prediction"].mean().to_dict()
	parity_gap = float(max(rates.values()) - min(rates.values())) if len(rates) > 1 else 0.0
	return {
		"window_size": int(len(logs)),
		"group_positive_rates": {key: float(value) for key, value in rates.items()},
		"parity_gap": parity_gap,
	}

