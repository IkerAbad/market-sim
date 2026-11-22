"""Threshold sensitivity for the stylized-fact table.

The pass/fail table uses explicit thresholds.  This module recomputes the pass
rate of each fact over the per-seed metrics under alternative thresholds.  It
answers a simple question: how much does the conclusion depend on the cut-off?
"""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

THRESHOLD_GRID: tuple[tuple[str, str, str, tuple[float, ...]], ...] = (
    ("Kurtosis", "kurtosis", ">", (3.0, 5.0, 10.0, 20.0)),
    ("ACF(returns, 1)", "acf_return_lag1", "abs<", (0.01, 0.02, 0.05, 0.10)),
    ("ACF(abs, 1)", "acf_abs_return_lag1", ">", (0.05, 0.10, 0.15, 0.20)),
    ("ACF(abs, 50)", "acf_abs_return_lag50", ">", (0.02, 0.05, 0.10, 0.15)),
    ("corr(volume, abs)", "corr_volume_abs_return", ">", (0.20, 0.30, 0.50, 0.60)),
    ("Tail ratio", "tail_exceedance_ratio", ">", (1.0, 5.0, 20.0, 50.0)),
)

NUMERIC_COLUMNS = (
    "kurtosis",
    "acf_return_lag1",
    "acf_abs_return_lag1",
    "acf_abs_return_lag50",
    "corr_volume_abs_return",
    "tail_exceedance_ratio",
)


@dataclass(frozen=True)
class ThresholdRow:
    """Pass rate for one fact under one threshold."""

    fact: str
    column: str
    direction: str
    threshold: float
    passes: int
    total: int
    rate: float


def load_metrics_csv(path: str | Path) -> list[dict[str, float]]:
    """Load the per-seed metrics CSV written by the ensemble runner."""
    rows: list[dict[str, float]] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("the CSV file has no header")
        missing = [name for name in NUMERIC_COLUMNS if name not in reader.fieldnames]
        if missing:
            raise ValueError(f"missing columns: {', '.join(missing)}")
        for raw in reader:
            row = {name: float(raw[name]) for name in NUMERIC_COLUMNS}
            rows.append(row)
    if not rows:
        raise ValueError("the CSV file has no data rows")
    return rows


def _passes(value: float, direction: str, threshold: float) -> bool:
    if direction == ">":
        return value > threshold
    if direction == "abs<":
        return abs(value) < threshold
    raise ValueError(f"unknown direction: {direction}")


def evaluate_thresholds(
    rows: Sequence[Mapping[str, float]],
    grid: Sequence[tuple[str, str, str, Sequence[float]]] = THRESHOLD_GRID,
) -> list[ThresholdRow]:
    """Count how many rows pass each fact under each threshold."""
    if not rows:
        raise ValueError("at least one row is required")
    output: list[ThresholdRow] = []
    for fact, column, direction, thresholds in grid:
        for threshold in thresholds:
            passes = sum(_passes(float(row[column]), direction, threshold) for row in rows)
            output.append(
                ThresholdRow(
                    fact=fact,
                    column=column,
                    direction=direction,
                    threshold=threshold,
                    passes=passes,
                    total=len(rows),
                    rate=passes / len(rows),
                )
            )
    return output


def format_threshold_markdown(rows: Sequence[ThresholdRow]) -> str:
    """Render the threshold table as Markdown."""
    lines = [
        "| Fact | Threshold | Seeds passing | Pass rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        if row.direction == "abs<":
            criterion = f"|value| < {row.threshold:g}"
        else:
            criterion = f"> {row.threshold:g}"
        lines.append(f"| {row.fact} | {criterion} | {row.passes}/{row.total} | {row.rate:.0%} |")
    return "\n".join(lines)


def write_threshold_csv(rows: Sequence[ThresholdRow], path: str | Path) -> Path:
    """Write the threshold table as a CSV file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["fact", "column", "direction", "threshold", "passes", "total", "rate"])
        for row in rows:
            writer.writerow(
                [
                    row.fact,
                    row.column,
                    row.direction,
                    f"{row.threshold:.10g}",
                    row.passes,
                    row.total,
                    f"{row.rate:.10g}",
                ]
            )
    return output


def threshold_report(rows: Sequence[ThresholdRow], command: str, source: str) -> str:
    """Build the Markdown report for the threshold sensitivity."""
    summary = format_threshold_markdown(rows)
    lowest = min(rows, key=lambda row: row.rate)
    return "\n".join(
        [
            "# Threshold sensitivity",
            "",
            "Command:",
            "",
            "```",
            command,
            "```",
            "",
            f"- Per-seed metrics: `{source}`",
            f"- Seeds: {rows[0].total}",
            "- Each row uses the same per-seed metrics and changes only the",
            "  threshold of one fact.",
            "",
            summary,
            "",
            "## Reading",
            "",
            "A high pass rate under a stricter threshold means the fact has a",
            "large margin.  A low pass rate means the conclusion depends on the",
            "original cut-off.  The strictest cell in this table is",
            f"{lowest.fact} at {lowest.rate:.0%} ({lowest.passes}/{lowest.total}).",
            "",
        ]
    )
