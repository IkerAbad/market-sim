"""Percentiles of the five price statistics under Gaussian noise.

The benchmark pass rates show that the original kurtosis and tail-ratio
thresholds are weak.  This module gives the null distribution of each statistic
so the thresholds can be read against it.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .benchmark_rates import FACT_KEYS
from .benchmarks import benchmark_metrics
from .config import MetricsParams


@dataclass(frozen=True)
class NullStatistic:
    """One statistic under Gaussian noise and its model value."""

    key: str
    label: str
    q05: float
    median: float
    q95: float
    model_value: float
    model_percentile: float


def null_statistics(
    params: MetricsParams,
    model_metrics: Mapping[str, float],
    n_series: int = 1000,
    n: int = 100000,
    seed: int = 123,
) -> tuple[NullStatistic, ...]:
    """Compute Gaussian percentiles and the percentile of the model value."""
    if n_series < 1:
        raise ValueError("n_series must be positive")
    if n < params.acf_lags + 1:
        raise ValueError("n must be longer than acf_lags")
    rng = np.random.default_rng(seed)
    samples: dict[str, list[float]] = {key: [] for key, _ in FACT_KEYS}
    for _ in range(n_series):
        metrics = benchmark_metrics(rng.normal(size=n), params)
        for key, _ in FACT_KEYS:
            samples[key].append(metrics[key])
    rows: list[NullStatistic] = []
    for key, label in FACT_KEYS:
        values = np.asarray(samples[key], dtype=float)
        q05, median, q95 = np.quantile(values, [0.05, 0.5, 0.95])
        model_value = float(model_metrics[key])
        percentile = float(np.mean(values < model_value))
        rows.append(
            NullStatistic(
                key=key,
                label=label,
                q05=float(q05),
                median=float(median),
                q95=float(q95),
                model_value=model_value,
                model_percentile=percentile,
            )
        )
    return tuple(rows)


def format_null_markdown(rows: Sequence[NullStatistic]) -> str:
    """Render the null distribution table as Markdown."""
    lines = [
        "| Statistic | Gaussian 5% | Median | 95% | Model | Model percentile |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row.label} | {row.q05:.4g} | {row.median:.4g} | {row.q95:.4g} | "
            f"{row.model_value:.4g} | {100.0 * row.model_percentile:.1f}% |"
        )
    return "\n".join(lines)


def write_null_csv(rows: Sequence[NullStatistic], path: str | Path) -> Path:
    """Write the null distribution table as a CSV file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["statistic", "q05", "median", "q95", "model", "percentile"])
        for row in rows:
            writer.writerow(
                [
                    row.key,
                    f"{row.q05:.10g}",
                    f"{row.median:.10g}",
                    f"{row.q95:.10g}",
                    f"{row.model_value:.10g}",
                    f"{row.model_percentile:.10g}",
                ]
            )
    return output
