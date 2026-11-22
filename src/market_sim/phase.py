"""Coarse parameter robustness map.

The map runs a small grid of ``activity_sigma`` and ``max_chartist_demand``
values over several seeds and counts how many of the six statistic rows pass in
each cell.  It is a scan, not a substitute for the 100,000-step baseline.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from itertools import product
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


def _float_metric(metrics: dict[str, float | int | None], key: str) -> float:
    value = metrics.get(key)
    if value is None:
        raise ValueError(f"metric {key!r} is missing")
    return float(value)


@dataclass(frozen=True)
class PhasePoint:
    """One cell and seed of the robustness map."""

    activity_sigma: float
    max_chartist_demand: float
    seed: int
    pass_count: int
    all_pass: bool
    metrics: dict[str, float]


@dataclass(frozen=True)
class PhaseSummary:
    """Aggregated robustness map."""

    activity_values: tuple[float, ...]
    chartist_values: tuple[float, ...]
    mean_pass: np.ndarray
    all_pass_count: np.ndarray
    n_seeds: int


def parse_values(spec: str) -> tuple[float, ...]:
    """Parse ``"0.5,0.75,1.0"`` into a tuple of finite non-negative floats."""
    values: list[float] = []
    for token in spec.split(","):
        text = token.strip()
        if not text:
            continue
        value = float(text)
        if not np.isfinite(value) or value < 0:
            raise ValueError(f"values must be finite and non-negative: {text!r}")
        values.append(value)
    if not values:
        raise ValueError("at least one value is required")
    return tuple(values)


def run_phase_point(
    config: SimulationConfig,
    activity_sigma: float,
    max_chartist_demand: float,
    seed: int,
) -> PhasePoint:
    """Run one grid cell for one seed."""
    model = replace(
        config.model,
        activity_sigma=activity_sigma,
        max_chartist_demand=max_chartist_demand,
    )
    point_config = replace(config, seed=seed, model=model)
    result = simulate(point_config)
    returns, volume = result.analysis_window()
    raw_metrics = compute_metrics(returns, volume, config.metrics)
    metrics = {key: _float_metric(raw_metrics, key) for key in _METRIC_KEYS}
    facts = evaluate_facts(raw_metrics, config.metrics)
    return PhasePoint(
        activity_sigma=activity_sigma,
        max_chartist_demand=max_chartist_demand,
        seed=seed,
        pass_count=sum(bool(row["passes"]) for row in facts),
        all_pass=all_facts_pass(facts),
        metrics=metrics,
    )


def run_phase_grid(
    config: SimulationConfig,
    activity_values: Sequence[float],
    chartist_values: Sequence[float],
    seeds: Iterable[int],
    jobs: int = 1,
) -> list[PhasePoint]:
    """Run every cell and seed, optionally with a process pool."""
    seed_list = sorted(set(seeds))
    if not seed_list:
        raise ValueError("at least one seed is required")
    tasks = [
        (activity, chartist, seed)
        for activity, chartist in product(activity_values, chartist_values)
        for seed in seed_list
    ]
    if jobs <= 1 or len(tasks) == 1:
        return [
            run_phase_point(config, activity, chartist, seed) for activity, chartist, seed in tasks
        ]
    workers = min(jobs, len(tasks))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(run_phase_point, config, activity, chartist, seed)
            for activity, chartist, seed in tasks
        ]
        return [future.result() for future in futures]


def summarize_phase(points: Sequence[PhasePoint]) -> PhaseSummary:
    """Aggregate the grid into mean pass counts and all-pass counts."""
    if not points:
        raise ValueError("at least one point is required")
    activity_values = tuple(sorted({point.activity_sigma for point in points}))
    chartist_values = tuple(sorted({point.max_chartist_demand for point in points}))
    mean_pass = np.zeros((len(chartist_values), len(activity_values)))
    all_pass_count = np.zeros_like(mean_pass, dtype=int)
    counts = np.zeros_like(mean_pass, dtype=int)
    activity_index = {value: index for index, value in enumerate(activity_values)}
    chartist_index = {value: index for index, value in enumerate(chartist_values)}
    for point in points:
        i = chartist_index[point.max_chartist_demand]
        j = activity_index[point.activity_sigma]
        mean_pass[i, j] += point.pass_count
        all_pass_count[i, j] += int(point.all_pass)
        counts[i, j] += 1
    if int(counts.min()) == 0:
        raise ValueError("the grid is incomplete")
    if not np.all(counts == counts.flat[0]):
        raise ValueError("every cell must have the same number of seeds")
    return PhaseSummary(
        activity_values=activity_values,
        chartist_values=chartist_values,
        mean_pass=mean_pass / counts,
        all_pass_count=all_pass_count,
        n_seeds=int(counts.flat[0]),
    )


def write_phase_csv(points: Sequence[PhasePoint], path: str | Path) -> Path:
    """Write one row per cell and seed."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "activity_sigma",
                "max_chartist_demand",
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
        for point in points:
            writer.writerow(
                [
                    f"{point.activity_sigma:.10g}",
                    f"{point.max_chartist_demand:.10g}",
                    point.seed,
                    point.pass_count,
                    int(point.all_pass),
                    f"{float(point.metrics['kurtosis']):.10g}",
                    f"{float(point.metrics['acf_return_lag1']):.10g}",
                    f"{float(point.metrics['acf_abs_return_lag1']):.10g}",
                    f"{float(point.metrics['acf_abs_return_lag50']):.10g}",
                    f"{float(point.metrics['corr_volume_abs_return']):.10g}",
                    f"{float(point.metrics['tail_exceedance_ratio']):.10g}",
                ]
            )
    return output


def format_phase_markdown(summary: PhaseSummary) -> str:
    """Render the mean pass-count map as a Markdown table."""
    header = (
        "| max_chartist_demand \\ activity_sigma | "
        + " | ".join(f"{value:g}" for value in summary.activity_values)
        + " |"
    )
    separator = "| ---: | " + " | ".join("---:" for _ in summary.activity_values) + " |"
    lines = [header, separator]
    for i, chartist in enumerate(summary.chartist_values):
        cells = " | ".join(
            f"{summary.mean_pass[i, j]:.2f} ({summary.all_pass_count[i, j]}/{summary.n_seeds})"
            for j in range(len(summary.activity_values))
        )
        lines.append(f"| {chartist:g} | {cells} |")
    return "\n".join(lines)


def plot_phase_heatmap(summary: PhaseSummary, path: str | Path) -> Path:
    """Plot the mean pass-count map as a heatmap."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(7.5, 5.2))
    image = axis.imshow(
        summary.mean_pass,
        origin="lower",
        aspect="auto",
        vmin=0.0,
        vmax=6.0,
        cmap="viridis",
    )
    for i in range(len(summary.chartist_values)):
        for j in range(len(summary.activity_values)):
            axis.text(
                j,
                i,
                f"{summary.mean_pass[i, j]:.1f}",
                ha="center",
                va="center",
                color="white" if summary.mean_pass[i, j] < 3.5 else "black",
                fontsize=9,
            )
    axis.set_xticks(range(len(summary.activity_values)))
    axis.set_xticklabels([f"{value:g}" for value in summary.activity_values])
    axis.set_yticks(range(len(summary.chartist_values)))
    axis.set_yticklabels([f"{value:g}" for value in summary.chartist_values])
    axis.set_xlabel("activity_sigma")
    axis.set_ylabel("max_chartist_demand")
    axis.set_title("Mean number of passing statistics (of 6)")
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("mean pass count")
    if 1.0 in summary.activity_values and 0.1 in summary.chartist_values:
        j = summary.activity_values.index(1.0)
        i = summary.chartist_values.index(0.1)
        axis.add_patch(
            Rectangle(
                (j - 0.5, i - 0.5),
                1.0,
                1.0,
                fill=False,
                edgecolor="#d62728",
                linewidth=2.0,
            )
        )
    figure.savefig(output, bbox_inches="tight")
    plt.close(figure)
    return output


def phase_report(summary: PhaseSummary, command: str) -> str:
    """Build the Markdown report for the phase diagram."""
    return "\n".join(
        [
            "# Parameter robustness map",
            "",
            "Command:",
            "",
            "```",
            command,
            "```",
            "",
            f"- Seeds per cell: {summary.n_seeds}",
            "- Cells show the mean number of passing statistic rows and, in",
            "  parentheses, the number of seeds where all six rows pass.",
            "- The red outline marks the baseline cell.",
            "",
            format_phase_markdown(summary),
            "",
            "## Reading",
            "",
            "This is a coarse scan, not the 100,000-step baseline.  It shows the",
            "region where the model satisfies the criteria and the two main",
            "failure directions.  Low activity reduces clustering and breaks fact",
            "3.  High chartist demand creates return autocorrelation and breaks",
            "fact 2.",
            "",
        ]
    )
