"""Discrimination on the additional facts that do not need volume.

The five price facts are not the only diagnostics.  This module compares the
model, GARCH and Gaussian noise on leverage, gain/loss asymmetry, the DFA Hurst
exponent and aggregational Gaussianity.
"""

from __future__ import annotations

import csv
from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from functools import partial
from pathlib import Path

import numpy as np

from .config import SimulationConfig
from .discrimination import auc
from .extra_facts import non_volume_metrics
from .market import simulate

ADDITIONAL_KEYS: tuple[tuple[str, str, bool], ...] = (
    ("leverage_lag1", "Leverage effect", False),
    ("gain_loss_volatility_ratio", "Gain/loss asymmetry", True),
    ("dfa_hurst_abs", "DFA Hurst exponent", True),
    ("aggregational_ratio", "Aggregational ratio", False),
)

Generator = Callable[[int, int], np.ndarray]


@dataclass(frozen=True)
class AdditionalDiscriminationRow:
    """Medians and AUC for one additional fact."""

    key: str
    label: str
    model_median: float
    garch_median: float
    gaussian_median: float
    auc_garch: float
    auc_gaussian: float


def run_model_seed(config: SimulationConfig, seed: int) -> tuple[int, dict[str, float]]:
    """Simulate one seed and compute the four non-volume additional facts."""
    result = simulate(replace(config, seed=seed))
    returns, _ = result.analysis_window()
    return seed, non_volume_metrics(returns)


def run_model_ensemble(
    config: SimulationConfig, seeds: Iterable[int], jobs: int = 1
) -> list[dict[str, float]]:
    """Run the additional-fact metrics over several seeds."""
    seed_list = sorted(set(seeds))
    if not seed_list:
        raise ValueError("at least one seed is required")
    if jobs <= 1 or len(seed_list) == 1:
        return [run_model_seed(config, seed)[1] for seed in seed_list]
    workers = min(jobs, len(seed_list))
    worker = partial(run_model_seed, config)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return [metrics for _, metrics in pool.map(worker, seed_list)]


def samples_from_generator(
    generator: Generator,
    n_series: int,
    n: int,
    base_seed: int = 0,
) -> list[dict[str, float]]:
    """Generate synthetic series and compute the four additional facts."""
    if n_series < 1:
        raise ValueError("n_series must be positive")
    return [non_volume_metrics(generator(n, base_seed + index)) for index in range(n_series)]


def additional_discrimination_rows(
    model: Sequence[Mapping[str, float]],
    garch: Sequence[Mapping[str, float]],
    gaussian: Sequence[Mapping[str, float]],
) -> tuple[AdditionalDiscriminationRow, ...]:
    """Compute medians and AUC for each non-volume additional fact."""
    if not model or not garch or not gaussian:
        raise ValueError("all three samples must be non-empty")
    rows: list[AdditionalDiscriminationRow] = []
    for key, label, higher in ADDITIONAL_KEYS:
        model_values = np.asarray([float(row[key]) for row in model], dtype=float)
        garch_values = np.asarray([float(row[key]) for row in garch], dtype=float)
        gaussian_values = np.asarray([float(row[key]) for row in gaussian], dtype=float)
        rows.append(
            AdditionalDiscriminationRow(
                key=key,
                label=label,
                model_median=float(np.median(model_values)),
                garch_median=float(np.median(garch_values)),
                gaussian_median=float(np.median(gaussian_values)),
                auc_garch=auc(model_values, garch_values, higher),
                auc_gaussian=auc(model_values, gaussian_values, higher),
            )
        )
    return tuple(rows)


def format_additional_discrimination_markdown(
    rows: Sequence[AdditionalDiscriminationRow],
) -> str:
    """Render the additional-fact discrimination table as Markdown."""
    lines = [
        "| Additional fact | Model median | GARCH median | Gaussian median | "
        "AUC vs GARCH | AUC vs Gaussian |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row.label} | {row.model_median:.4g} | {row.garch_median:.4g} | "
            f"{row.gaussian_median:.4g} | {row.auc_garch:.3f} | {row.auc_gaussian:.3f} |"
        )
    return "\n".join(lines)


def write_additional_discrimination_csv(
    rows: Sequence[AdditionalDiscriminationRow], path: str | Path
) -> Path:
    """Write the additional-fact discrimination table as a CSV file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "fact",
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
