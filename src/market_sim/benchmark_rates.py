"""Pass rates of the five price facts across many synthetic series.

A single benchmark series can pass by luck.  This module repeats each benchmark
over many seeds and reports the fraction of series that pass each fact.
"""

from __future__ import annotations

import csv
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .benchmarks import benchmark_metrics, evaluate_benchmark
from .config import MetricsParams

FACT_KEYS: tuple[tuple[str, str], ...] = (
    ("kurtosis", "Kurtosis"),
    ("acf_return_lag1", "ACF(returns, 1)"),
    ("acf_abs_return_lag1", "ACF(abs, 1)"),
    ("acf_abs_return_lag50", "ACF(abs, 50)"),
    ("tail_exceedance_ratio", "Tail ratio"),
)

Generator = Callable[[int, int], np.ndarray]


@dataclass(frozen=True)
class FactRate:
    """Pass count for one fact across a set of series."""

    key: str
    label: str
    passes: int
    total: int

    @property
    def rate(self) -> float:
        return self.passes / self.total


@dataclass(frozen=True)
class BenchmarkRate:
    """Pass rates for one benchmark or for the model."""

    name: str
    description: str
    n_series: int
    facts: tuple[FactRate, ...]
    all_pass: int


def rate_metrics(
    name: str,
    description: str,
    metrics_list: Sequence[dict[str, float]],
    params: MetricsParams,
) -> BenchmarkRate:
    """Count per-fact passes over a list of metric mappings."""
    if not metrics_list:
        raise ValueError("at least one series is required")
    counts = [0] * len(FACT_KEYS)
    all_pass = 0
    for metrics in metrics_list:
        point = evaluate_benchmark(name, description, metrics, params)
        for index, passed in enumerate(point.passes):
            counts[index] += int(passed)
        all_pass += int(point.pass_count == len(FACT_KEYS))
    facts = tuple(
        FactRate(key=key, label=label, passes=counts[index], total=len(metrics_list))
        for index, (key, label) in enumerate(FACT_KEYS)
    )
    return BenchmarkRate(
        name=name,
        description=description,
        n_series=len(metrics_list),
        facts=facts,
        all_pass=all_pass,
    )


def metrics_from_generator(
    generator: Generator,
    params: MetricsParams,
    n_series: int,
    n: int,
    base_seed: int = 0,
) -> list[dict[str, float]]:
    """Generate ``n_series`` series and return their five metrics."""
    if n_series < 1:
        raise ValueError("n_series must be positive")
    return [benchmark_metrics(generator(n, base_seed + index), params) for index in range(n_series)]


def metrics_from_metrics_csv(path: str | Path) -> list[dict[str, float]]:
    """Load the five price metrics from a per-seed metrics CSV."""
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("the metrics CSV has no rows")
    return [{key: float(row[key]) for key, _ in FACT_KEYS} for row in rows]


def rate_generator(
    name: str,
    description: str,
    generator: Generator,
    params: MetricsParams,
    n_series: int,
    n: int,
    base_seed: int = 0,
) -> BenchmarkRate:
    """Generate ``n_series`` series and count the facts that pass."""
    metrics_list = metrics_from_generator(generator, params, n_series, n, base_seed)
    return rate_metrics(name, description, metrics_list, params)


def rates_from_metrics_csv(
    path: str | Path,
    name: str,
    description: str,
    params: MetricsParams,
) -> BenchmarkRate:
    """Build a rate row from a per-seed metrics CSV."""
    return rate_metrics(name, description, metrics_from_metrics_csv(path), params)


def format_rates_markdown(rates: Sequence[BenchmarkRate]) -> str:
    """Render the pass-rate table as Markdown."""
    header = "| Series | " + " | ".join(label for _, label in FACT_KEYS) + " | All five |"
    separator = "| --- | " + " | ".join("---:" for _ in FACT_KEYS) + " | ---: |"
    lines = [header, separator]
    for rate in rates:
        cells = " | ".join(f"{fact.passes}/{fact.total}" for fact in rate.facts)
        lines.append(f"| {rate.name} | {cells} | {rate.all_pass}/{rate.n_series} |")
    return "\n".join(lines)


def write_rates_csv(rates: Sequence[BenchmarkRate], path: str | Path) -> Path:
    """Write one row per benchmark with pass counts."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    header = ["series", "n_series", *(key for key, _ in FACT_KEYS), "all_five"]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for rate in rates:
            writer.writerow(
                [
                    rate.name,
                    rate.n_series,
                    *(fact.passes for fact in rate.facts),
                    rate.all_pass,
                ]
            )
    return output
