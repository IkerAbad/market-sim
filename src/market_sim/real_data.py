"""Compare the model with a user-supplied return series.

No market data are bundled with the repository.  The user passes a CSV with a
return column, or a price/close column that is converted to log returns.
"""

from __future__ import annotations

import csv
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from .benchmarks import benchmark_metrics, evaluate_benchmark
from .config import MetricsParams

_PRICE_COLUMNS = {"price", "close", "adj_close", "adj close"}


def load_returns_csv(path: str | Path, column: str = "return") -> np.ndarray:
    """Load returns from a CSV column, or log returns from a price column."""
    values: list[float] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("the CSV file has no header")
        if column not in reader.fieldnames:
            raise ValueError(
                f"column {column!r} not found. Available columns: {', '.join(reader.fieldnames)}"
            )
        for row in reader:
            text = row[column].strip()
            if not text:
                continue
            value = float(text)
            if math.isfinite(value):
                values.append(value)
    if len(values) < 2:
        raise ValueError("the column must contain at least two values")
    if column.lower() in _PRICE_COLUMNS:
        prices = np.asarray(values, dtype=float)
        if np.any(prices <= 0):
            raise ValueError("prices must be positive")
        return np.diff(np.log(prices))
    return np.asarray(values, dtype=float)


def compare_metrics(
    model_returns: Sequence[float],
    data_returns: Sequence[float],
    params: MetricsParams,
) -> list[dict[str, Any]]:
    """Compare the five price facts of the model and a data series."""
    model = benchmark_metrics(np.asarray(model_returns, dtype=float), params)
    data = benchmark_metrics(np.asarray(data_returns, dtype=float), params)
    model_point = evaluate_benchmark("model", "", model, params)
    data_point = evaluate_benchmark("data", "", data, params)
    rows: list[dict[str, Any]] = []
    keys = (
        ("kurtosis", "Kurtosis"),
        ("acf_return_lag1", "ACF(returns, 1)"),
        ("acf_abs_return_lag1", "ACF(abs, 1)"),
        ("acf_abs_return_lag50", "ACF(abs, 50)"),
        ("tail_exceedance_ratio", "Tail ratio"),
    )
    for (key, label), model_pass, data_pass in zip(
        keys, model_point.passes, data_point.passes, strict=True
    ):
        rows.append(
            {
                "statistic": label,
                "model": float(model[key]),
                "data": float(data[key]),
                "difference": float(data[key]) - float(model[key]),
                "model_pass": model_pass,
                "data_pass": data_pass,
            }
        )
    return rows


def format_comparison_markdown(rows: Sequence[dict[str, Any]]) -> str:
    """Render the model-versus-data table as Markdown."""
    lines = [
        "| Statistic | Model | Data | Data minus model | Model pass | Data pass |",
        "| --- | ---: | ---: | ---: | :---: | :---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['statistic']} | {row['model']:.4g} | {row['data']:.4g} | "
            f"{row['difference']:+.4g} | {'yes' if row['model_pass'] else 'no'} | "
            f"{'yes' if row['data_pass'] else 'no'} |"
        )
    return "\n".join(lines)


def write_comparison_csv(rows: Sequence[dict[str, Any]], path: str | Path) -> Path:
    """Write the comparison as a CSV file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["statistic", "model", "data", "difference", "model_pass", "data_pass"])
        for row in rows:
            writer.writerow(
                [
                    row["statistic"],
                    f"{float(row['model']):.10g}",
                    f"{float(row['data']):.10g}",
                    f"{float(row['difference']):.10g}",
                    int(bool(row["model_pass"])),
                    int(bool(row["data_pass"])),
                ]
            )
    return output
