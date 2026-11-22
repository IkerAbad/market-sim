"""Stylized-fact statistics.

The functions here are intentionally small and explicit.  Autocorrelations use
the full-sample variance in the denominator (the usual biased estimator), and
kurtosis is the raw fourth standardised moment, so the normal benchmark is
3.0.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np

from .config import MetricsParams


def _as_1d_finite(x: np.ndarray | Iterable[float], name: str) -> np.ndarray:
    array = np.asarray(x, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if array.size < 2:
        raise ValueError(f"{name} must contain at least two observations")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains non-finite values")
    return array


def autocorrelation(x: np.ndarray | Iterable[float], max_lag: int) -> np.ndarray:
    """Sample autocorrelation from lag 0 to ``max_lag``.

    The series is centred on its sample mean.  Each numerator is divided by the
    full sum of squared deviations, not by the number of overlapping pairs.
    """
    array = _as_1d_finite(x, "x")
    if max_lag < 0:
        raise ValueError("max_lag cannot be negative")
    if max_lag >= array.size:
        raise ValueError("max_lag must be smaller than the series length")
    centred = array - array.mean()
    denominator = float(np.dot(centred, centred))
    if denominator == 0.0:
        raise ValueError("autocorrelation is undefined for a constant series")
    result = np.empty(max_lag + 1, dtype=float)
    result[0] = 1.0
    for lag in range(1, max_lag + 1):
        result[lag] = float(np.dot(centred[lag:], centred[:-lag]) / denominator)
    return result


def kurtosis(x: np.ndarray | Iterable[float]) -> float:
    """Raw kurtosis with population moments.  A normal variable has value 3."""
    array = _as_1d_finite(x, "x")
    centred = array - array.mean()
    variance = float(np.mean(centred**2))
    if variance == 0.0:
        raise ValueError("kurtosis is undefined for a constant series")
    return float(np.mean(centred**4) / variance**2)


def tail_exceedance_ratio(x: np.ndarray | Iterable[float], sigma: float = 4.0) -> float:
    """Empirical two-sided tail probability divided by the normal one.

    A value above 1 means that observations beyond ``sigma`` standard
    deviations are more frequent than under a normal distribution with the same
    mean and variance.
    """
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    array = _as_1d_finite(x, "x")
    standard_deviation = float(array.std())
    if standard_deviation == 0.0:
        raise ValueError("tail ratio is undefined for a constant series")
    empirical = float(np.mean(np.abs(array - array.mean()) > sigma * standard_deviation))
    normal = math.erfc(sigma / math.sqrt(2.0))
    return empirical / normal


def compute_metrics(
    returns: np.ndarray | Iterable[float],
    volume: np.ndarray | Iterable[float],
    params: MetricsParams,
) -> dict[str, float | int | None]:
    """Compute the statistics used in the results table."""
    r = _as_1d_finite(returns, "returns")
    v = np.asarray(volume, dtype=float)
    if v.ndim != 1 or v.size != r.size:
        raise ValueError("returns and volume must be one-dimensional and equally long")
    if not np.all(np.isfinite(v)):
        raise ValueError("volume contains non-finite values")
    if r.size <= params.acf_lags:
        raise ValueError("the series must be longer than acf_lags")
    if float(v.std()) == 0.0:
        raise ValueError("volume is constant")

    centred = r - r.mean()
    absolute = np.abs(centred)
    acf_returns = autocorrelation(r, params.acf_lags)
    acf_absolute = autocorrelation(absolute, params.acf_lags)

    def lag_value(values: np.ndarray, lag: int) -> float | None:
        return float(values[lag]) if lag < values.size else None

    empirical_tail = float(np.mean(np.abs(centred) > params.tail_sigma * float(r.std())))
    normal_tail = math.erfc(params.tail_sigma / math.sqrt(2.0))

    return {
        "n_observations": int(r.size),
        "mean_return": float(r.mean()),
        "std_return": float(r.std()),
        "kurtosis": kurtosis(r),
        "acf_return_lag1": lag_value(acf_returns, 1),
        "acf_abs_return_lag1": lag_value(acf_absolute, 1),
        "acf_abs_return_lag10": lag_value(acf_absolute, 10),
        "acf_abs_return_lag50": lag_value(acf_absolute, 50),
        "acf_abs_return_lag100": lag_value(acf_absolute, 100),
        "acf_abs_return_lag200": lag_value(acf_absolute, 200),
        "corr_volume_abs_return": float(np.corrcoef(v, absolute)[0, 1]),
        "tail_sigma": float(params.tail_sigma),
        "tail_probability": empirical_tail,
        "normal_tail_probability": float(normal_tail),
        "tail_exceedance_ratio": empirical_tail / normal_tail,
    }


def _metric_float(metrics: Mapping[str, float | int | None], key: str) -> float:
    value = metrics.get(key)
    if value is None:
        raise ValueError(f"metric {key!r} is required")
    return float(value)


def evaluate_facts(
    metrics: Mapping[str, float | int | None], params: MetricsParams
) -> list[dict[str, Any]]:
    """Map statistics to the five stylized facts and their criteria."""
    rows: list[dict[str, Any]] = []
    kurtosis_value = _metric_float(metrics, "kurtosis")
    return_acf1 = _metric_float(metrics, "acf_return_lag1")
    abs_acf1 = _metric_float(metrics, "acf_abs_return_lag1")
    abs_acf50 = _metric_float(metrics, "acf_abs_return_lag50")
    volume_corr = _metric_float(metrics, "corr_volume_abs_return")
    tail_ratio = _metric_float(metrics, "tail_exceedance_ratio")

    def add(
        fact: int,
        statistic: str,
        value: float,
        criterion: str,
        passes: bool,
    ) -> None:
        rows.append(
            {
                "fact": fact,
                "statistic": statistic,
                "value": float(value),
                "criterion": criterion,
                "passes": bool(passes),
            }
        )

    add(
        1,
        "Kurtosis",
        kurtosis_value,
        f"> {params.kurtosis_threshold:g}",
        kurtosis_value > params.kurtosis_threshold,
    )
    add(
        2,
        "ACF(returns, lag 1)",
        return_acf1,
        f"abs(value) < {params.return_acf_threshold:g}",
        abs(return_acf1) < params.return_acf_threshold,
    )
    add(
        3,
        "ACF(abs(returns), lag 1)",
        abs_acf1,
        f"> {params.abs_acf_lag1_threshold:g}",
        abs_acf1 > params.abs_acf_lag1_threshold,
    )
    add(
        3,
        "ACF(abs(returns), lag 50)",
        abs_acf50,
        f"> {params.abs_acf_lag50_threshold:g}",
        abs_acf50 > params.abs_acf_lag50_threshold,
    )
    add(
        4,
        "corr(volume, abs(returns))",
        volume_corr,
        f"> {params.volume_corr_threshold:g}",
        volume_corr > params.volume_corr_threshold,
    )
    add(
        5,
        f"P(abs(r) > {params.tail_sigma:g} sd) / P_normal",
        tail_ratio,
        f"> {params.tail_ratio_threshold:g}",
        tail_ratio > params.tail_ratio_threshold,
    )
    return rows


def format_markdown_table(rows: list[dict[str, Any]]) -> str:
    """Render the fact table as GitHub-flavoured Markdown."""
    lines = [
        "| Fact | Statistic | Value | Criterion | Pass |",
        "| ---: | --- | ---: | --- | :---: |",
    ]
    for row in rows:
        value = f"{float(row['value']):.4g}"
        passes = "yes" if row["passes"] else "no"
        lines.append(
            f"| {row['fact']} | {row['statistic']} | {value} | {row['criterion']} | {passes} |"
        )
    return "\n".join(lines)


def all_facts_pass(rows: list[dict[str, Any]]) -> bool:
    """True when every row in the table passes its criterion."""
    if not rows:
        raise ValueError("at least one fact row is required")
    return all(bool(row["passes"]) for row in rows)
