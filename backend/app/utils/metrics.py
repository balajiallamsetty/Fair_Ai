"""Fairness and bias metric utilities."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Return a stable ratio while avoiding divide-by-zero errors."""

    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def _selection_rate(values: pd.Series) -> float:
    """Return the mean selection rate of a binary-like series."""

    return float(pd.to_numeric(values, errors="coerce").fillna(0).mean())


def demographic_parity(y_pred: pd.Series, sensitive: pd.Series) -> dict[str, Any]:
    """Compute demographic parity across sensitive groups."""

    frame = pd.DataFrame({"y_pred": y_pred, "sensitive": sensitive.astype(str)})
    rates = frame.groupby("sensitive")["y_pred"].mean().to_dict()
    if len(rates) < 2:
        return {"group_rates": rates, "difference": 0.0, "privileged_group": None, "unprivileged_group": None}

    privileged_group = max(rates, key=rates.get)
    unprivileged_group = min(rates, key=rates.get)
    return {
        "group_rates": {key: float(value) for key, value in rates.items()},
        "difference": float(rates[privileged_group] - rates[unprivileged_group]),
        "privileged_group": privileged_group,
        "unprivileged_group": unprivileged_group,
    }


def equal_opportunity(y_true: pd.Series, y_pred: pd.Series, sensitive: pd.Series) -> dict[str, Any]:
    """Compute equal opportunity difference using true positive rates."""

    frame = pd.DataFrame(
        {"y_true": pd.to_numeric(y_true, errors="coerce"), "y_pred": pd.to_numeric(y_pred, errors="coerce"), "sensitive": sensitive.astype(str)}
    )
    rates: dict[str, float] = {}
    for group, subset in frame.groupby("sensitive"):
        positives = subset[subset["y_true"] == 1]
        rates[group] = _selection_rate(positives["y_pred"]) if not positives.empty else 0.0
    if len(rates) < 2:
        return {"true_positive_rates": rates, "difference": 0.0}
    return {
        "true_positive_rates": {key: float(value) for key, value in rates.items()},
        "difference": float(max(rates.values()) - min(rates.values())),
    }


def disparate_impact(y_pred: pd.Series, sensitive: pd.Series) -> dict[str, Any]:
    """Compute disparate impact ratio between least and most selected groups."""

    dp = demographic_parity(y_pred, sensitive)
    rates = dp["group_rates"]
    if len(rates) < 2:
        return {"ratio": 1.0, "group_rates": rates}
    min_group = min(rates, key=rates.get)
    max_group = max(rates, key=rates.get)
    ratio = _safe_ratio(rates[min_group], rates[max_group])
    return {"ratio": ratio, "group_rates": rates, "reference_group": max_group, "impacted_group": min_group}


def bias_score_from_components(components: list[float]) -> float:
    """Aggregate several normalized fairness components into a single score."""

    if not components:
        return 0.0
    bounded = np.clip(np.array(components, dtype=float), 0.0, 1.0)
    return float(bounded.mean())
