"""Finite-sample sensitivity of the stylized facts.

The baseline uses 100,000 observations.  This module reruns the same model at
several sample lengths to check whether the facts depend on that choice.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from .config import SimulationConfig
from .market import simulate
from .stylized import all_facts_pass, compute_metrics, evaluate_facts

_METRIC_KEYS = (
    "kurtosis",
    "acf_return_lag1",
    "acf_abs_return_lag1",
    "acf_abs_return_lag50",
    "corr_volume_abs_return",
    "tail_exceedance_ratio",
)
_STATISTIC_LABELS = (
    "Kurtosis",
    "ACF(returns, 1)",
    "ACF(abs, 1)",
    "ACF(abs, 50)",
    "corr(volume, abs)",
    "Tail ratio",
)


@dataclass(frozen=True)
class SampleSizePoint:
    """One sample length and seed."""

    size: int
    seed: int
    metrics: dict[str, float]
    passes: tuple[bool, ...]
    pass_count: int
    all_pass: bool


@dataclass(frozen=True)
class SampleSizeSummary:
    """Aggregated finite-sample table."""

    sizes: tuple[int, ...]
    n_seeds: int
    mean_metrics: dict[str, np.ndarray]
    pass_counts: np.ndarray
    all_pass_count: np.ndarray


def _float_metric(metrics: dict[str, float | int | None], key: str) -> float:
    value = metrics.get(key)
    if value is None:
        raise ValueError(f"metric {key!r} is missing")
    return float(value)


def run_sample_size_point(config: SimulationConfig, size: int, seed: int) -> SampleSizePoint:
    """Run one sample length for one seed."""
    if size < 2:
        raise ValueError("size must be at least 2")
    burn_in = min(config.burn_in, max(0, size // 10))
    point_config = replace(config, n_steps=size, burn_in=burn_in, seed=seed)
    result = simulate(point_config)
    returns, volume = result.analysis_window()
    raw_metrics = compute_metrics(returns, volume, config.metrics)
    metrics = {key: _float_metric(raw_metrics, key) for key in _METRIC_KEYS}
    facts = evaluate_facts(raw_metrics, config.metrics)
    passes = tuple(bool(row["passes"]) for row in facts)
    return SampleSizePoint(
        size=size,
        seed=seed,
        metrics=metrics,
        passes=passes,
        pass_count=sum(passes),
        all_pass=all_facts_pass(facts),
    )


def run_sample_size_grid(
    config: SimulationConfig,
    sizes: Iterable[int],
    seeds: Iterable[int],
    jobs: int = 1,
) -> list[SampleSizePoint]:
    """Run every sample length and seed."""
    size_list = sorted(set(sizes))
    seed_list = sorted(set(seeds))
    if not size_list:
        raise ValueError("at least one size is required")
    if not seed_list:
        raise ValueError("at least one seed is required")
    tasks = [(size, seed) for size in size_list for seed in seed_list]
    if jobs <= 1 or len(tasks) == 1:
        return [run_sample_size_point(config, size, seed) for size, seed in tasks]
    workers = min(jobs, len(tasks))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_sample_size_point, config, size, seed) for size, seed in tasks]
        return [future.result() for future in futures]


def summarize_sample_size(
    results: Sequence[SampleSizePoint],
) -> SampleSizeSummary:
    """Aggregate the sample-size results."""
    if not results:
        raise ValueError("at least one result is required")
    sizes = tuple(sorted({result.size for result in results}))
    n_seeds = len({result.seed for result in results})
    mean_metrics = {
        key: np.asarray(
            [
                np.mean([result.metrics[key] for result in results if result.size == size])
                for size in sizes
            ],
            dtype=float,
        )
        for key in _METRIC_KEYS
    }
    pass_counts = np.zeros((len(sizes), len(_STATISTIC_LABELS)), dtype=int)
    for result in results:
        row = sizes.index(result.size)
        for column, passed in enumerate(result.passes):
            pass_counts[row, column] += int(passed)
    all_pass_count = np.zeros(len(sizes), dtype=int)
    for result in results:
        if result.all_pass:
            all_pass_count[sizes.index(result.size)] += 1
    return SampleSizeSummary(
        sizes=sizes,
        n_seeds=n_seeds,
        mean_metrics=mean_metrics,
        pass_counts=pass_counts,
        all_pass_count=all_pass_count,
    )


def format_sample_size_markdown(summary: SampleSizeSummary) -> str:
    """Render the sample-size table as Markdown."""
    lines = [
        (
            "| Size | Seeds | Mean kurtosis | Mean ACF(returns, 1) | "
            "Mean ACF(abs, 1) | Mean ACF(abs, 50) | Mean corr | Mean tail | "
            "Mean pass | All-pass seeds |"
        ),
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, size in enumerate(summary.sizes):
        metrics = summary.mean_metrics
        mean_pass = summary.pass_counts[index].sum() / summary.n_seeds
        lines.append(
            f"| {size} | {summary.n_seeds} | {metrics['kurtosis'][index]:.3f} | "
            f"{metrics['acf_return_lag1'][index]:.4f} | "
            f"{metrics['acf_abs_return_lag1'][index]:.4f} | "
            f"{metrics['acf_abs_return_lag50'][index]:.4f} | "
            f"{metrics['corr_volume_abs_return'][index]:.4f} | "
            f"{metrics['tail_exceedance_ratio'][index]:.2f} | "
            f"{mean_pass:.2f} | {summary.all_pass_count[index]}/{summary.n_seeds} |"
        )
    return "\n".join(lines)


def write_sample_size_csv(results: Sequence[SampleSizePoint], path: str | Path) -> Path:
    """Write one row per sample length and seed."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "size",
                "seed",
                "pass_count",
                "all_pass",
                *_METRIC_KEYS,
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result.size,
                    result.seed,
                    result.pass_count,
                    int(result.all_pass),
                    *(f"{result.metrics[key]:.10g}" for key in _METRIC_KEYS),
                ]
            )
    return output


def sample_size_report(summary: SampleSizeSummary, command: str) -> str:
    """Build the Markdown report for the sample-size sensitivity."""
    return "\n".join(
        [
            "# Sample-size sensitivity",
            "",
            "Command:",
            "",
            "```",
            command,
            "```",
            "",
            f"- Seeds per size: {summary.n_seeds}",
            "- Each row uses the same model and a different number of simulated steps.",
            "",
            format_sample_size_markdown(summary),
            "",
            "## Reading",
            "",
            "Kurtosis is the most sample-dependent statistic because it is driven",
            "by rare large returns.  The autocorrelations, the volume correlation",
            "and the tail ratio are expected to be more stable.  The table shows",
            "whether the 100,000-step baseline is a special case or one point on",
            "a stable curve.",
            "",
        ]
    )
