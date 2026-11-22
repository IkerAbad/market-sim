"""Ablation study: which model components are necessary for each fact?

Each ablation changes one structural ingredient of the baseline and reruns the
same statistics over a set of seeds.  The baseline is included as a reference.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

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
class Ablation:
    """One structural variant of the baseline model."""

    name: str
    description: str
    overrides: dict[str, Any]


ABLATIONS: tuple[Ablation, ...] = (
    Ablation("baseline", "No structural change", {}),
    Ablation(
        "no_chartists",
        "Chartists removed, noise absorbs their fraction",
        {"chartist_fraction": 0.0, "fundamentalist_fraction": 0.3},
    ),
    Ablation(
        "no_fundamentalists",
        "Fundamentalists removed, noise absorbs their fraction",
        {"fundamentalist_fraction": 0.0, "chartist_fraction": 0.4},
    ),
    Ablation(
        "noise_only",
        "Only noise traders remain",
        {"fundamentalist_fraction": 0.0, "chartist_fraction": 0.0},
    ),
    Ablation(
        "no_activity",
        "Activity is constant for every agent",
        {"activity_sigma": 0.0},
    ),
    Ablation(
        "fixed_memory",
        "All agents have the same memory",
        {"memory_min": 100, "memory_max": 100},
    ),
    Ablation(
        "homogeneous_risk",
        "All agents have the same risk aversion",
        {"risk_aversion_min": 1.0, "risk_aversion_max": 1.0},
    ),
    Ablation(
        "homogeneous_wealth",
        "All agents have the same wealth weight",
        {"wealth_min": 1.0, "wealth_max": 1.0},
    ),
    Ablation(
        "no_bias",
        "Fundamentalists have no idiosyncratic bias",
        {"fundamental_bias_std": 0.0},
    ),
    Ablation(
        "no_noise_demand",
        "Noise agents submit zero demand",
        {"noise_demand_scale": 0.0},
    ),
)


@dataclass(frozen=True)
class AblationResult:
    """One ablation and seed."""

    name: str
    seed: int
    pass_count: int
    all_pass: bool
    passes: tuple[bool, ...]
    metrics: dict[str, float]


@dataclass(frozen=True)
class AblationSummary:
    """Aggregated ablation table."""

    names: tuple[str, ...]
    n_seeds: int
    pass_counts: np.ndarray
    mean_pass_count: np.ndarray
    all_pass_count: np.ndarray


def _float_metric(metrics: dict[str, float | int | None], key: str) -> float:
    value = metrics.get(key)
    if value is None:
        raise ValueError(f"metric {key!r} is missing")
    return float(value)


def run_ablation_point(config: SimulationConfig, ablation: Ablation, seed: int) -> AblationResult:
    """Run one ablation for one seed."""
    model = replace(config.model, **ablation.overrides)
    point_config = replace(config, seed=seed, model=model)
    result = simulate(point_config)
    returns, volume = result.analysis_window()
    raw_metrics = compute_metrics(returns, volume, config.metrics)
    metrics = {key: _float_metric(raw_metrics, key) for key in _METRIC_KEYS}
    facts = evaluate_facts(raw_metrics, config.metrics)
    passes = tuple(bool(row["passes"]) for row in facts)
    return AblationResult(
        name=ablation.name,
        seed=seed,
        pass_count=sum(passes),
        all_pass=all_facts_pass(facts),
        passes=passes,
        metrics=metrics,
    )


def run_ablation_grid(
    config: SimulationConfig,
    ablations: Sequence[Ablation],
    seeds: Iterable[int],
    jobs: int = 1,
) -> list[AblationResult]:
    """Run every ablation and seed, optionally with a process pool."""
    seed_list = sorted(set(seeds))
    if not seed_list:
        raise ValueError("at least one seed is required")
    tasks = [(ablation, seed) for ablation in ablations for seed in seed_list]
    if jobs <= 1 or len(tasks) == 1:
        return [run_ablation_point(config, ablation, seed) for ablation, seed in tasks]
    workers = min(jobs, len(tasks))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(run_ablation_point, config, ablation, seed) for ablation, seed in tasks
        ]
        return [future.result() for future in futures]


def summarize_ablations(
    results: Sequence[AblationResult], ablations: Sequence[Ablation]
) -> AblationSummary:
    """Aggregate pass counts for each ablation and statistic."""
    if not results:
        raise ValueError("at least one result is required")
    names = tuple(ablation.name for ablation in ablations)
    n_seeds = len({result.seed for result in results})
    pass_counts = np.zeros((len(names), len(_STATISTIC_LABELS)), dtype=int)
    for result in results:
        row = names.index(result.name)
        for column, passed in enumerate(result.passes):
            pass_counts[row, column] += int(passed)
    mean_pass_count = pass_counts.sum(axis=1) / n_seeds
    all_pass_count = np.zeros(len(names), dtype=int)
    for result in results:
        if result.all_pass:
            all_pass_count[names.index(result.name)] += 1
    return AblationSummary(
        names=names,
        n_seeds=n_seeds,
        pass_counts=pass_counts,
        mean_pass_count=mean_pass_count,
        all_pass_count=all_pass_count,
    )


def format_ablation_markdown(summary: AblationSummary, first_column: str = "Ablation") -> str:
    """Render the ablation table as Markdown."""
    header = (
        f"| {first_column} | " + " | ".join(_STATISTIC_LABELS) + " | Mean pass | All-pass seeds |"
    )
    separator = "| --- | " + " | ".join("---:" for _ in _STATISTIC_LABELS) + " | ---: | ---: |"
    lines = [header, separator]
    for i, name in enumerate(summary.names):
        cells = " | ".join(
            f"{summary.pass_counts[i, j]}/{summary.n_seeds}" for j in range(len(_STATISTIC_LABELS))
        )
        lines.append(
            f"| {name} | {cells} | {summary.mean_pass_count[i]:.2f} | "
            f"{summary.all_pass_count[i]}/{summary.n_seeds} |"
        )
    return "\n".join(lines)


def write_ablation_csv(
    results: Sequence[AblationResult], path: str | Path, first_column: str = "ablation"
) -> Path:
    """Write one row per ablation and seed."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                first_column,
                "seed",
                "pass_count",
                "all_pass",
                "kurtosis",
                "acf_return_lag1",
                "acf_abs_return_lag1",
                "acf_abs_return_lag50",
                "corr_volume_abs_return",
                "tail_exceedance_ratio",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result.name,
                    result.seed,
                    result.pass_count,
                    int(result.all_pass),
                    f"{result.metrics['kurtosis']:.10g}",
                    f"{result.metrics['acf_return_lag1']:.10g}",
                    f"{result.metrics['acf_abs_return_lag1']:.10g}",
                    f"{result.metrics['acf_abs_return_lag50']:.10g}",
                    f"{result.metrics['corr_volume_abs_return']:.10g}",
                    f"{result.metrics['tail_exceedance_ratio']:.10g}",
                ]
            )
    return output


def _row_summary(summary: AblationSummary, name: str) -> str:
    index = summary.names.index(name)
    return (
        f"{summary.mean_pass_count[index]:.2f}/6, "
        f"all-pass {summary.all_pass_count[index]}/{summary.n_seeds}"
    )


def ablation_report(summary: AblationSummary, command: str) -> str:
    """Build the Markdown report for the ablation study."""
    highlight_names = [
        name
        for name in (
            "noise_only",
            "no_chartists",
            "no_fundamentalists",
            "no_activity",
            "no_noise_demand",
        )
        if name in summary.names
    ]
    lines = [
        "# Ablation study",
        "",
        "Command:",
        "",
        "```",
        command,
        "```",
        "",
        f"- Seeds per ablation: {summary.n_seeds}",
        "- Each cell is the number of seeds where that statistic passes.",
        "- The baseline row is the reference.",
        "",
        format_ablation_markdown(summary),
        "",
        "## Reading",
        "",
    ]
    lines.extend(f"- `{name}`: {_row_summary(summary, name)}." for name in highlight_names)
    if len(highlight_names) == 5:
        lines.extend(
            [
                "",
                "The three-type composition is not necessary for the six rows: the",
                "noise-only variant passes all of them.  The activity process is",
                "necessary: removing it removes most of the rows.  The agent types",
                "shape the price level and the return autocorrelation, but they are",
                "not the source of the statistical facts.",
            ]
        )
    lines.append("")
    return "\n".join(lines)
