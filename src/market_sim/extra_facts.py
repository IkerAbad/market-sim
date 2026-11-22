"""Additional stylized facts that are not part of the original five.

These diagnostics are reported to show what the model does not reproduce.
They are deliberately separated from the main table so that a failure here is
visible and is not confused with the five target facts.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from .stylized import correlation

NumericSeries = np.ndarray | Sequence[float]


def leverage_effect(returns: NumericSeries, lag: int = 1) -> float:
    """Correlation between a return and future absolute return.

    A negative value is the leverage effect.  The absolute future return is
    centred before the correlation.
    """
    r = np.asarray(returns, dtype=float)
    if r.ndim != 1 or r.size < 3:
        raise ValueError("returns must be a one-dimensional series")
    if not np.all(np.isfinite(r)):
        raise ValueError("returns contain non-finite values")
    if lag < 1 or lag >= r.size:
        raise ValueError("lag must be between 1 and the series length")
    future = np.abs(r[lag:] - r[lag:].mean())
    return correlation(r[:-lag], future)


def leverage_profile(returns: NumericSeries, max_lag: int = 10) -> np.ndarray:
    """Leverage correlation for lags 1 through ``max_lag``."""
    if max_lag < 1:
        raise ValueError("max_lag must be positive")
    return np.asarray(
        [leverage_effect(returns, lag=lag) for lag in range(1, max_lag + 1)],
        dtype=float,
    )


def gain_loss_asymmetry(returns: NumericSeries) -> dict[str, float | int]:
    """Compare the volatility and mean absolute size of losses and gains."""
    r = np.asarray(returns, dtype=float)
    if r.ndim != 1 or r.size < 4:
        raise ValueError("returns must be a one-dimensional series of length 4 or more")
    if not np.all(np.isfinite(r)):
        raise ValueError("returns contain non-finite values")
    negative = r[r < 0]
    positive = r[r > 0]
    if negative.size < 2 or positive.size < 2:
        raise ValueError("both positive and negative returns are required")
    negative_scale = float(np.max(np.abs(negative)))
    positive_scale = float(np.max(np.abs(positive)))
    negative_std = negative_scale * float((negative / negative_scale).std(ddof=1))
    positive_std = positive_scale * float((positive / positive_scale).std(ddof=1))
    if negative_std == 0.0 or positive_std == 0.0:
        raise ValueError("both sides need non-zero variance")
    negative_mean_abs = negative_scale * float(np.mean(np.abs(negative) / negative_scale))
    positive_mean = positive_scale * float(np.mean(positive / positive_scale))
    return {
        "negative_count": int(negative.size),
        "positive_count": int(positive.size),
        "volatility_ratio": negative_std / positive_std,
        "mean_abs_ratio": negative_mean_abs / positive_mean,
    }


def dfa_hurst(series: NumericSeries, scales: Sequence[int] | None = None) -> float:
    """Detrended fluctuation analysis exponent.

    White noise gives an exponent close to 0.5.  Values above 0.5 indicate
    persistent long-range correlations in the input series.
    """
    values = np.asarray(series, dtype=float)
    if values.ndim != 1 or values.size < 32:
        raise ValueError("series must be a one-dimensional series of length 32 or more")
    if not np.all(np.isfinite(values)):
        raise ValueError("series contains non-finite values")
    scale = float(np.max(np.abs(values)))
    if scale == 0.0:
        raise ValueError("DFA is undefined for a constant series")
    values = values / scale
    if np.std(values) == 0:
        raise ValueError("DFA is undefined for a constant series")

    profile = np.cumsum(values - values.mean())
    n = profile.size
    if scales is None:
        max_power = int(np.floor(np.log2(n // 4)))
        if max_power < 3:
            raise ValueError("series is too short for the default DFA scales")
        scale_values = 2 ** np.arange(3, max_power + 1)
    else:
        scale_values = np.asarray(scales, dtype=int)
    if scale_values.size < 3 or np.any(scale_values < 2):
        raise ValueError("at least three scales of length 2 or more are required")

    fluctuations: list[float] = []
    used_scales: list[int] = []
    for window in scale_values:
        n_segments = n // int(window)
        if n_segments < 2:
            continue
        segments = profile[: n_segments * int(window)].reshape(n_segments, int(window))
        positions = np.arange(int(window), dtype=float)
        position_mean = positions.mean()
        denominator = float(np.sum((positions - position_mean) ** 2))
        segment_mean = segments.mean(axis=1, keepdims=True)
        slope = (
            np.sum((segments - segment_mean) * (positions - position_mean), axis=1) / denominator
        )
        intercept = segment_mean[:, 0] - slope * position_mean
        trend = intercept[:, None] + slope[:, None] * positions
        residual = segments - trend
        fluctuation = float(np.sqrt(np.mean(residual**2)))
        if fluctuation > 0:
            fluctuations.append(fluctuation)
            used_scales.append(int(window))
    if len(fluctuations) < 3:
        raise ValueError("not enough valid DFA scales")
    slope = np.polyfit(np.log(used_scales), np.log(fluctuations), 1)[0]
    return float(slope)


def volume_volatility_lead_lag(
    returns: NumericSeries,
    volume: NumericSeries,
    max_lag: int = 10,
) -> tuple[int, float, dict[int, float]]:
    """Find the lag where volume correlates most with absolute returns.

    The correlation is ``corr(volume[t], abs(return[t + lag]))``.  Positive
    lags mean volume leads volatility.
    """
    r = np.asarray(returns, dtype=float)
    v = np.asarray(volume, dtype=float)
    if r.ndim != 1 or v.ndim != 1 or r.size != v.size:
        raise ValueError("returns and volume must be one-dimensional and equally long")
    if r.size < 10 or not np.all(np.isfinite(r)) or not np.all(np.isfinite(v)):
        raise ValueError("returns and volume must be finite")
    if max_lag < 0 or max_lag >= r.size:
        raise ValueError("max_lag must be between 0 and the series length")
    absolute = np.abs(r - r.mean())
    correlations: dict[int, float] = {}
    for lag in range(-max_lag, max_lag + 1):
        if lag > 0:
            left = v[:-lag]
            right = absolute[lag:]
        elif lag < 0:
            left = v[-lag:]
            right = absolute[:lag]
        else:
            left = v
            right = absolute
        if left.size < 3:
            continue
        try:
            correlations[lag] = correlation(left, right)
        except ValueError:
            continue
    if not correlations:
        raise ValueError("no valid lag could be computed")
    best_lag = max(correlations, key=lambda key: correlations[key])
    return best_lag, correlations[best_lag], correlations


def additional_metrics(returns: NumericSeries, volume: NumericSeries) -> dict[str, float | int]:
    """Compute all additional diagnostics in one call."""
    r = np.asarray(returns, dtype=float)
    leverage = leverage_effect(r, lag=1)
    profile = leverage_profile(r, max_lag=10)
    asymmetry = gain_loss_asymmetry(r)
    hurst = dfa_hurst(np.abs(r - r.mean()))
    best_lag, best_corr, _ = volume_volatility_lead_lag(r, volume, max_lag=10)
    return {
        "leverage_lag1": leverage,
        "leverage_mean_1_10": float(profile.mean()),
        "gain_loss_volatility_ratio": float(asymmetry["volatility_ratio"]),
        "gain_loss_mean_abs_ratio": float(asymmetry["mean_abs_ratio"]),
        "dfa_hurst_abs": hurst,
        "volume_volatility_best_lag": best_lag,
        "volume_volatility_best_corr": best_corr,
    }


def evaluate_additional_facts(
    metrics: dict[str, float | int],
) -> list[dict[str, Any]]:
    """Evaluate the additional facts with explicit, arbitrary thresholds."""
    rows = [
        {
            "fact": "Leverage effect",
            "statistic": "corr(r[t], abs(r[t+1]))",
            "value": float(metrics["leverage_lag1"]),
            "criterion": "< -0.02",
            "passes": float(metrics["leverage_lag1"]) < -0.02,
        },
        {
            "fact": "Gain/loss asymmetry",
            "statistic": "std(losses) / std(gains)",
            "value": float(metrics["gain_loss_volatility_ratio"]),
            "criterion": "> 1.05",
            "passes": float(metrics["gain_loss_volatility_ratio"]) > 1.05,
        },
        {
            "fact": "Long memory of abs(returns)",
            "statistic": "DFA Hurst exponent",
            "value": float(metrics["dfa_hurst_abs"]),
            "criterion": "> 0.60",
            "passes": float(metrics["dfa_hurst_abs"]) > 0.60,
        },
        {
            "fact": "Volume leads volatility",
            "statistic": "best lag of corr(volume, abs(return))",
            "value": int(metrics["volume_volatility_best_lag"]),
            "criterion": "> 0",
            "passes": int(metrics["volume_volatility_best_lag"]) > 0,
        },
    ]
    return rows


def format_additional_table(rows: list[dict[str, Any]]) -> str:
    """Render the additional-facts table as Markdown."""
    lines = [
        "| Additional fact | Statistic | Value | Criterion | Pass |",
        "| --- | --- | ---: | --- | :---: |",
    ]
    for row in rows:
        value = f"{float(row['value']):.4g}"
        passes = "yes" if row["passes"] else "no"
        lines.append(
            f"| {row['fact']} | {row['statistic']} | {value} | {row['criterion']} | {passes} |"
        )
    return "\n".join(lines)


def write_additional_csv(rows: list[dict[str, Any]], path: str | Path) -> Path:
    """Write the additional-facts table as a CSV file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["fact", "statistic", "value", "criterion", "passes"])
        for row in rows:
            writer.writerow(
                [
                    row["fact"],
                    row["statistic"],
                    f"{float(row['value']):.10g}",
                    row["criterion"],
                    1 if row["passes"] else 0,
                ]
            )
    return output
