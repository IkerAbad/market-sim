"""Discriminative power of the price facts between the model and benchmarks.

A pass rate answers whether a fact passes.  It does not answer how much the
fact separates the model from a benchmark.  This module computes the area under
the ROC curve for each statistic and a grid of pass rates over the two weak
tail thresholds.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from .benchmark_rates import FACT_KEYS
from .benchmarks import evaluate_benchmark
from .config import MetricsParams

FACT_DIRECTIONS: dict[str, str] = {
    "kurtosis": "higher",
    "acf_return_lag1": "lower_abs",
    "acf_abs_return_lag1": "higher",
    "acf_abs_return_lag50": "higher",
    "tail_exceedance_ratio": "higher",
}


@dataclass(frozen=True)
class DiscriminationRow:
    """Median values and AUC for one statistic."""

    key: str
    label: str
    direction: str
    model_median: float
    garch_median: float
    gaussian_median: float
    auc_garch: float
    auc_gaussian: float


@dataclass(frozen=True)
class ThresholdCell:
    """All-five pass counts for one pair of tail thresholds."""

    kurtosis: float
    tail: float
    model_pass: int
    model_total: int
    garch_pass: int
    garch_total: int
    gaussian_pass: int
    gaussian_total: int


def _transform(values: Sequence[float], direction: str) -> tuple[np.ndarray, bool]:
    array = np.asarray(values, dtype=float)
    if direction == "higher":
        return array, True
    if direction == "lower_abs":
        return np.abs(array), False
    raise ValueError(f"unknown direction {direction!r}")


def auc(
    model: np.ndarray | Sequence[float],
    benchmark: np.ndarray | Sequence[float],
    higher_is_better: bool = True,
) -> float:
    """Area under the ROC curve from pairwise comparisons.

    A value of 0.5 means that the statistic does not separate the two samples.
    A value of 1.0 means that every model value is on the model side of every
    benchmark value.
    """
    left = np.asarray(model, dtype=float)
    right = np.asarray(benchmark, dtype=float)
    if left.size == 0 or right.size == 0:
        raise ValueError("both samples must be non-empty")
    wins = 0.0
    for left_value in left:
        for right_value in right:
            if left_value == right_value:
                wins += 0.5
            elif (left_value > right_value) == higher_is_better:
                wins += 1.0
    return wins / (left.size * right.size)


def discrimination_rows(
    model: Sequence[Mapping[str, float]],
    garch: Sequence[Mapping[str, float]],
    gaussian: Sequence[Mapping[str, float]],
) -> tuple[DiscriminationRow, ...]:
    """Compute medians and AUC for each price statistic."""
    if not model or not garch or not gaussian:
        raise ValueError("all three samples must be non-empty")
    rows: list[DiscriminationRow] = []
    for key, label in FACT_KEYS:
        direction = FACT_DIRECTIONS[key]
        model_values = [float(row[key]) for row in model]
        garch_values = [float(row[key]) for row in garch]
        gaussian_values = [float(row[key]) for row in gaussian]
        model_transformed, higher = _transform(model_values, direction)
        garch_transformed, _ = _transform(garch_values, direction)
        gaussian_transformed, _ = _transform(gaussian_values, direction)
        rows.append(
            DiscriminationRow(
                key=key,
                label=label,
                direction=direction,
                model_median=float(np.median(model_values)),
                garch_median=float(np.median(garch_values)),
                gaussian_median=float(np.median(gaussian_values)),
                auc_garch=auc(model_transformed, garch_transformed, higher),
                auc_gaussian=auc(model_transformed, gaussian_transformed, higher),
            )
        )
    return tuple(rows)


def _pass_count(rows: Sequence[Mapping[str, float]], params: MetricsParams) -> int:
    count = 0
    for row in rows:
        metrics = {key: float(row[key]) for key, _ in FACT_KEYS}
        point = evaluate_benchmark("sample", "", metrics, params)
        count += int(point.pass_count == len(FACT_KEYS))
    return count


def threshold_grid(
    model: Sequence[Mapping[str, float]],
    garch: Sequence[Mapping[str, float]],
    gaussian: Sequence[Mapping[str, float]],
    params: MetricsParams,
    kurtosis_thresholds: Sequence[float] = (3.0, 4.0, 5.0, 6.0, 8.0, 10.0),
    tail_thresholds: Sequence[float] = (1.0, 2.0, 5.0, 10.0, 20.0, 50.0),
) -> tuple[ThresholdCell, ...]:
    """All-five pass counts over a grid of the two weak tail thresholds."""
    if not model or not garch or not gaussian:
        raise ValueError("all three samples must be non-empty")
    cells: list[ThresholdCell] = []
    for kurtosis in kurtosis_thresholds:
        for tail in tail_thresholds:
            strict = replace(
                params,
                kurtosis_threshold=float(kurtosis),
                tail_ratio_threshold=float(tail),
            )
            cells.append(
                ThresholdCell(
                    kurtosis=float(kurtosis),
                    tail=float(tail),
                    model_pass=_pass_count(model, strict),
                    model_total=len(model),
                    garch_pass=_pass_count(garch, strict),
                    garch_total=len(garch),
                    gaussian_pass=_pass_count(gaussian, strict),
                    gaussian_total=len(gaussian),
                )
            )
    return tuple(cells)


def format_discrimination_markdown(rows: Sequence[DiscriminationRow]) -> str:
    """Render the AUC table as Markdown."""
    lines = [
        "| Statistic | Model median | GARCH median | Gaussian median | "
        "AUC vs GARCH | AUC vs Gaussian |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row.label} | {row.model_median:.4g} | {row.garch_median:.4g} | "
            f"{row.gaussian_median:.4g} | {row.auc_garch:.3f} | {row.auc_gaussian:.3f} |"
        )
    return "\n".join(lines)


def format_grid_markdown(cells: Sequence[ThresholdCell]) -> str:
    """Render the threshold grid as Markdown."""
    lines = [
        "| Kurtosis > | Tail ratio > | Model | GARCH | Gaussian |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for cell in cells:
        lines.append(
            f"| {cell.kurtosis:g} | {cell.tail:g} | "
            f"{cell.model_pass}/{cell.model_total} | "
            f"{cell.garch_pass}/{cell.garch_total} | "
            f"{cell.gaussian_pass}/{cell.gaussian_total} |"
        )
    return "\n".join(lines)


def write_discrimination_csv(rows: Sequence[DiscriminationRow], path: str | Path) -> Path:
    """Write the AUC table as a CSV file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "statistic",
                "model_median",
                "garch_median",
                "gaussian_median",
                "auc_garch",
                "auc_gaussian",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.key,
                    f"{row.model_median:.10g}",
                    f"{row.garch_median:.10g}",
                    f"{row.gaussian_median:.10g}",
                    f"{row.auc_garch:.6f}",
                    f"{row.auc_gaussian:.6f}",
                ]
            )
    return output


def write_grid_csv(cells: Sequence[ThresholdCell], path: str | Path) -> Path:
    """Write the threshold grid as a CSV file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "kurtosis_threshold",
                "tail_threshold",
                "model_pass",
                "model_total",
                "garch_pass",
                "garch_total",
                "gaussian_pass",
                "gaussian_total",
            ]
        )
        for cell in cells:
            writer.writerow(
                [
                    f"{cell.kurtosis:g}",
                    f"{cell.tail:g}",
                    cell.model_pass,
                    cell.model_total,
                    cell.garch_pass,
                    cell.garch_total,
                    cell.gaussian_pass,
                    cell.gaussian_total,
                ]
            )
    return output


def plot_threshold_grid(
    cells: Sequence[ThresholdCell],
    kurtosis_thresholds: Sequence[float],
    tail_thresholds: Sequence[float],
    path: str | Path,
) -> Path:
    """Plot model, GARCH and Gaussian pass rates over the threshold grid."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    shape = (len(kurtosis_thresholds), len(tail_thresholds))
    model = np.zeros(shape)
    garch = np.zeros(shape)
    gaussian = np.zeros(shape)
    for cell in cells:
        row = list(kurtosis_thresholds).index(cell.kurtosis)
        column = list(tail_thresholds).index(cell.tail)
        model[row, column] = cell.model_pass / cell.model_total
        garch[row, column] = cell.garch_pass / cell.garch_total
        gaussian[row, column] = cell.gaussian_pass / cell.gaussian_total

    figure, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), constrained_layout=True)
    panels = (
        (model, "Model pass rate", "viridis", 0.0, 1.0),
        (garch, "GARCH pass rate", "viridis", 0.0, 1.0),
        (model - garch, "Model minus GARCH", "coolwarm", -1.0, 1.0),
    )
    for axis, (values, title, colour, low, high) in zip(axes, panels, strict=True):
        image = axis.imshow(values, aspect="auto", cmap=colour, vmin=low, vmax=high)
        axis.set_title(title)
        axis.set_xticks(range(len(tail_thresholds)))
        axis.set_xticklabels([f"{value:g}" for value in tail_thresholds])
        axis.set_yticks(range(len(kurtosis_thresholds)))
        axis.set_yticklabels([f"{value:g}" for value in kurtosis_thresholds])
        axis.set_xlabel("Tail ratio threshold")
        axis.set_ylabel("Kurtosis threshold")
        for row in range(shape[0]):
            for column in range(shape[1]):
                value = values[row, column]
                text = f"{value:.2f}" if title != "Model minus GARCH" else f"{value:+.2f}"
                axis.text(
                    column,
                    row,
                    text,
                    ha="center",
                    va="center",
                    color="black" if abs(value) < 0.6 else "white",
                    fontsize=7,
                )
        figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    figure.savefig(output, dpi=160)
    plt.close(figure)
    return output
