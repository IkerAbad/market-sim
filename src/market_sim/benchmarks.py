"""Synthetic benchmarks for the five price facts.

The benchmarks show what simpler return-generating processes do.  They are not
agent-based models and they have no volume, so the volume fact is omitted from
the comparison.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .config import MetricsParams
from .stylized import autocorrelation, kurtosis, tail_exceedance_ratio


@dataclass(frozen=True)
class BenchmarkPoint:
    """Statistics for one synthetic series."""

    name: str
    description: str
    metrics: dict[str, float]
    passes: tuple[bool, ...]
    pass_count: int


def gaussian_returns(n: int, seed: int = 1) -> np.ndarray:
    """Independent standard normal returns."""
    if n < 1:
        raise ValueError("n must be positive")
    return np.random.default_rng(seed).normal(size=n)


def student_t_returns(n: int, df: float = 5.0, seed: int = 2) -> np.ndarray:
    """Independent Student-t returns."""
    if n < 1:
        raise ValueError("n must be positive")
    if df <= 2:
        raise ValueError("df must be greater than 2")
    return np.random.default_rng(seed).standard_t(df, size=n)


def garch11_returns(
    n: int,
    omega: float = 1e-6,
    alpha: float = 0.08,
    beta: float = 0.90,
    seed: int = 3,
) -> np.ndarray:
    """GARCH(1,1) returns with Gaussian innovations."""
    if n < 1:
        raise ValueError("n must be positive")
    if omega <= 0 or alpha < 0 or beta < 0:
        raise ValueError("omega must be positive and alpha and beta non-negative")
    if alpha + beta >= 1:
        raise ValueError("alpha + beta must be smaller than 1")
    rng = np.random.default_rng(seed)
    shocks = rng.normal(size=n)
    variance = np.empty(n)
    returns = np.empty(n)
    variance[0] = omega / (1.0 - alpha - beta)
    returns[0] = np.sqrt(variance[0]) * shocks[0]
    for t in range(1, n):
        variance[t] = omega + alpha * returns[t - 1] ** 2 + beta * variance[t - 1]
        returns[t] = np.sqrt(variance[t]) * shocks[t]
    return returns


def benchmark_metrics(returns: np.ndarray, params: MetricsParams) -> dict[str, float]:
    """Compute the five price facts for a return series."""
    values = np.asarray(returns, dtype=float)
    if values.ndim != 1 or values.size < params.acf_lags + 1:
        raise ValueError("returns must be longer than acf_lags")
    if not np.all(np.isfinite(values)):
        raise ValueError("returns contain non-finite values")
    centred = values - values.mean()
    absolute = np.abs(centred)
    acf_returns = autocorrelation(values, params.acf_lags)
    acf_absolute = autocorrelation(absolute, params.acf_lags)
    return {
        "kurtosis": kurtosis(values),
        "acf_return_lag1": float(acf_returns[1]),
        "acf_abs_return_lag1": float(acf_absolute[1]),
        "acf_abs_return_lag50": float(acf_absolute[50]),
        "tail_exceedance_ratio": tail_exceedance_ratio(values, sigma=params.tail_sigma),
    }


def evaluate_benchmark(
    name: str, description: str, metrics: dict[str, float], params: MetricsParams
) -> BenchmarkPoint:
    """Evaluate the five price facts for a benchmark."""
    passes = (
        metrics["kurtosis"] > params.kurtosis_threshold,
        abs(metrics["acf_return_lag1"]) < params.return_acf_threshold,
        metrics["acf_abs_return_lag1"] > params.abs_acf_lag1_threshold,
        metrics["acf_abs_return_lag50"] > params.abs_acf_lag50_threshold,
        metrics["tail_exceedance_ratio"] > params.tail_ratio_threshold,
    )
    return BenchmarkPoint(
        name=name,
        description=description,
        metrics=metrics,
        passes=passes,
        pass_count=sum(passes),
    )


def format_benchmark_markdown(points: Sequence[BenchmarkPoint]) -> str:
    """Render the benchmark table as Markdown."""
    lines = [
        (
            "| Series | Kurtosis | ACF(returns, 1) | ACF(abs, 1) | "
            "ACF(abs, 50) | Tail ratio | Facts passing |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for point in points:
        metrics = point.metrics
        lines.append(
            f"| {point.name} | {metrics['kurtosis']:.4g} | "
            f"{metrics['acf_return_lag1']:.4g} | "
            f"{metrics['acf_abs_return_lag1']:.4g} | "
            f"{metrics['acf_abs_return_lag50']:.4g} | "
            f"{metrics['tail_exceedance_ratio']:.4g} | "
            f"{point.pass_count}/5 |"
        )
    return "\n".join(lines)


def write_benchmark_csv(points: Sequence[BenchmarkPoint], path: str | Path) -> Path:
    """Write the benchmark table as a CSV file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "series",
                "kurtosis",
                "acf_return_lag1",
                "acf_abs_return_lag1",
                "acf_abs_return_lag50",
                "tail_exceedance_ratio",
                "pass_count",
            ]
        )
        for point in points:
            writer.writerow(
                [
                    point.name,
                    f"{point.metrics['kurtosis']:.10g}",
                    f"{point.metrics['acf_return_lag1']:.10g}",
                    f"{point.metrics['acf_abs_return_lag1']:.10g}",
                    f"{point.metrics['acf_abs_return_lag50']:.10g}",
                    f"{point.metrics['tail_exceedance_ratio']:.10g}",
                    point.pass_count,
                ]
            )
    return output
