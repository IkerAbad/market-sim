"""Descriptive diagnostics for the price gap and the volume series.

The five target facts are about returns.  These diagnostics describe the price
level around the fundamental value and the shape of the volume series.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from .stylized import autocorrelation, correlation, kurtosis


def price_diagnostics(log_prices: Sequence[float], fundamental_value: float) -> dict[str, float]:
    """Summarize the log-price gap around the fundamental value."""
    prices = np.asarray(log_prices, dtype=float)
    if prices.ndim != 1 or prices.size < 3:
        raise ValueError("log_prices must be a one-dimensional series")
    if not np.all(np.isfinite(prices)):
        raise ValueError("log_prices contain non-finite values")
    if fundamental_value <= 0:
        raise ValueError("fundamental_value must be positive")
    gap = prices - np.log(fundamental_value)
    span = float(np.max(gap) - np.min(gap))
    if span == 0.0:
        raise ValueError("price diagnostics are undefined for a constant gap")
    scaled = (gap - gap.min()) / span
    previous = scaled[:-1]
    following = scaled[1:]
    previous_centred = previous - previous.mean()
    following_centred = following - following.mean()
    denominator = float(np.dot(previous_centred, previous_centred))
    phi = float(np.dot(previous_centred, following_centred) / denominator)
    half_life = float(-np.log(2.0) / np.log(phi)) if 0.0 < phi < 1.0 else float("nan")
    return {
        "price_min": float(np.exp(prices.min())),
        "price_max": float(np.exp(prices.max())),
        "price_final": float(np.exp(prices[-1])),
        "gap_mean": float(gap.mean()),
        "gap_std": float(gap.std()),
        "gap_min": float(gap.min()),
        "gap_max": float(gap.max()),
        "gap_ar1": phi,
        "gap_half_life": half_life,
    }


def volume_diagnostics(volume: Sequence[float], returns: Sequence[float]) -> dict[str, float]:
    """Summarize the volume series and its relation to absolute returns."""
    v = np.asarray(volume, dtype=float)
    r = np.asarray(returns, dtype=float)
    if v.ndim != 1 or r.ndim != 1 or v.size != r.size:
        raise ValueError("volume and returns must be one-dimensional and equally long")
    if v.size < 3 or not np.all(np.isfinite(v)) or not np.all(np.isfinite(r)):
        raise ValueError("volume and returns must be finite")
    if float(np.max(v)) == float(np.min(v)):
        raise ValueError("volume diagnostics are undefined for a constant series")
    acf = autocorrelation(v, 10)
    absolute = np.abs(r - r.mean())
    return {
        "volume_mean": float(v.mean()),
        "volume_std": float(v.std()),
        "volume_kurtosis": kurtosis(v),
        "volume_acf1": float(acf[1]),
        "volume_acf10": float(acf[10]),
        "corr_volume_abs_return": correlation(v, absolute),
    }


def run_diagnostics(
    log_prices: Sequence[float],
    returns: Sequence[float],
    volume: Sequence[float],
    fundamental_value: float,
) -> dict[str, float]:
    """Compute both diagnostic sets."""
    result = price_diagnostics(log_prices, fundamental_value)
    result.update(volume_diagnostics(volume, returns))
    return result


def format_diagnostics_markdown(metrics: dict[str, float]) -> str:
    """Render the diagnostics as a Markdown table."""
    labels = (
        ("price_min", "Minimum price"),
        ("price_max", "Maximum price"),
        ("price_final", "Final price"),
        ("gap_mean", "Mean log gap"),
        ("gap_std", "Log gap standard deviation"),
        ("gap_min", "Minimum log gap"),
        ("gap_max", "Maximum log gap"),
        ("gap_ar1", "Log gap AR(1) coefficient"),
        ("gap_half_life", "Log gap half-life (steps)"),
        ("volume_mean", "Mean volume"),
        ("volume_std", "Volume standard deviation"),
        ("volume_kurtosis", "Volume kurtosis"),
        ("volume_acf1", "Volume ACF(1)"),
        ("volume_acf10", "Volume ACF(10)"),
        ("corr_volume_abs_return", "corr(volume, abs(returns))"),
    )
    lines = ["| Statistic | Value |", "| --- | ---: |"]
    for key, label in labels:
        value = metrics[key]
        lines.append(f"| {label} | {value:.4g} |")
    return "\n".join(lines)


def write_diagnostics_csv(metrics: dict[str, float], path: str | Path) -> Path:
    """Write the diagnostics as a CSV file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["statistic", "value"])
        for key, value in metrics.items():
            writer.writerow([key, f"{value:.10g}"])
    return output
