"""Block stability of the six statistics within one simulation.

The baseline run is a single 100,000-step series.  A high full-sample kurtosis
could come from one short episode.  This module splits the analysis window into
contiguous blocks and recomputes the statistics in each block.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .config import MetricsParams
from .stylized import compute_metrics

METRIC_KEYS = (
    "kurtosis",
    "acf_return_lag1",
    "acf_abs_return_lag1",
    "acf_abs_return_lag50",
    "corr_volume_abs_return",
    "tail_exceedance_ratio",
)

METRIC_LABELS = {
    "kurtosis": "Kurtosis",
    "acf_return_lag1": "ACF(returns, lag 1)",
    "acf_abs_return_lag1": "ACF(abs(returns), lag 1)",
    "acf_abs_return_lag50": "ACF(abs(returns), lag 50)",
    "corr_volume_abs_return": "corr(volume, abs(returns))",
    "tail_exceedance_ratio": "P(abs(r) > 4 sd) / P_normal",
}

CRITERIA = {
    "kurtosis": ("min", "kurtosis_threshold"),
    "acf_return_lag1": ("abs_max", "return_acf_threshold"),
    "acf_abs_return_lag1": ("min", "abs_acf_lag1_threshold"),
    "acf_abs_return_lag50": ("min", "abs_acf_lag50_threshold"),
    "corr_volume_abs_return": ("min", "volume_corr_threshold"),
    "tail_exceedance_ratio": ("min", "tail_ratio_threshold"),
}


@dataclass(frozen=True)
class BlockMetrics:
    """Statistics for one contiguous block of the analysis window."""

    index: int
    start: int
    end: int
    n_observations: int
    metrics: dict[str, float]


def _bounds(length: int, n_blocks: int) -> list[tuple[int, int]]:
    edges = np.linspace(0, length, n_blocks + 1).astype(int)
    return [(int(edges[i]), int(edges[i + 1])) for i in range(n_blocks)]


def block_metrics(
    returns: np.ndarray | Sequence[float],
    volume: np.ndarray | Sequence[float],
    params: MetricsParams,
    n_blocks: int = 10,
) -> list[BlockMetrics]:
    """Compute the six statistics in each contiguous block."""
    r = np.asarray(returns, dtype=float)
    v = np.asarray(volume, dtype=float)
    if r.ndim != 1 or v.ndim != 1 or r.size != v.size:
        raise ValueError("returns and volume must be one-dimensional and equally long")
    if not np.all(np.isfinite(r)) or not np.all(np.isfinite(v)):
        raise ValueError("returns and volume must be finite")
    if n_blocks < 2:
        raise ValueError("n_blocks must be at least 2")
    if r.size < n_blocks * (params.acf_lags + 1):
        raise ValueError("each block must be longer than acf_lags")

    blocks: list[BlockMetrics] = []
    for index, (start, end) in enumerate(_bounds(r.size, n_blocks)):
        metrics = compute_metrics(r[start:end], v[start:end], params)
        values: dict[str, float] = {}
        for key in METRIC_KEYS:
            value = metrics[key]
            if value is None:
                raise ValueError(f"{key} is undefined in a block")
            values[key] = float(value)
        blocks.append(
            BlockMetrics(
                index=index + 1,
                start=start,
                end=end,
                n_observations=end - start,
                metrics=values,
            )
        )
    return blocks


def block_passes(key: str, value: float, params: MetricsParams) -> bool:
    """Return whether one statistic meets its full-sample criterion."""
    criterion = CRITERIA.get(key)
    if criterion is None:
        raise ValueError(f"unknown statistic {key!r}")
    direction, attribute = criterion
    threshold = float(getattr(params, attribute))
    if direction == "min":
        return value > threshold
    if direction == "abs_max":
        return abs(value) < threshold
    raise ValueError(f"unknown criterion direction {direction!r}")


def summarize_blocks(
    blocks: Sequence[BlockMetrics], params: MetricsParams
) -> dict[str, dict[str, float]]:
    """Summarize each statistic across blocks and count block-level passes."""
    if not blocks:
        raise ValueError("blocks cannot be empty")
    summary: dict[str, dict[str, float]] = {}
    for key in METRIC_KEYS:
        values = np.array([block.metrics[key] for block in blocks], dtype=float)
        passes = sum(block_passes(key, float(value), params) for value in values)
        summary[key] = {
            "mean": float(values.mean()),
            "min": float(values.min()),
            "max": float(values.max()),
            "std": float(values.std()),
            "passes": float(passes),
            "total": float(values.size),
        }
    return summary


def format_stability_markdown(blocks: Sequence[BlockMetrics], params: MetricsParams) -> str:
    """Render the per-block table and the block summary as Markdown."""
    header = (
        "| Block | Start | End | " + " | ".join(METRIC_LABELS[key] for key in METRIC_KEYS) + " |"
    )
    separator = "| ---: | ---: | ---: | " + " | ".join("---:" for _ in METRIC_KEYS) + " |"
    lines = [header, separator]
    for block in blocks:
        cells = " | ".join(f"{block.metrics[key]:.4g}" for key in METRIC_KEYS)
        lines.append(f"| {block.index} | {block.start} | {block.end} | {cells} |")
    summary = summarize_blocks(blocks, params)
    lines.extend(
        [
            "",
            "| Statistic | Mean | Min | Max | Blocks passing |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for key in METRIC_KEYS:
        row = summary[key]
        lines.append(
            f"| {METRIC_LABELS[key]} | {row['mean']:.4g} | {row['min']:.4g} | "
            f"{row['max']:.4g} | {int(row['passes'])}/{int(row['total'])} |"
        )
    return "\n".join(lines)


def write_stability_csv(blocks: Sequence[BlockMetrics], path: str | Path) -> Path:
    """Write the per-block statistics as a CSV file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["block", "start", "end", "n_observations", *METRIC_KEYS])
        for block in blocks:
            writer.writerow(
                [
                    block.index,
                    block.start,
                    block.end,
                    block.n_observations,
                    *(f"{block.metrics[key]:.10g}" for key in METRIC_KEYS),
                ]
            )
    return output
