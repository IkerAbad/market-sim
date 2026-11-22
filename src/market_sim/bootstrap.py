"""Moving-block bootstrap for the baseline statistics.

The stylized-fact table reports point estimates from one path.  This module
resamples contiguous blocks of that path to estimate the sampling distribution
of each statistic.  It measures within-series uncertainty, not uncertainty
about the model specification.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .config import MetricsParams
from .stylized import autocorrelation, correlation, kurtosis, tail_exceedance_ratio

STATISTIC_KEYS: tuple[tuple[str, str], ...] = (
    ("kurtosis", "Kurtosis"),
    ("acf_return_lag1", "ACF(returns, lag 1)"),
    ("acf_abs_return_lag1", "ACF(abs(returns), lag 1)"),
    ("acf_abs_return_lag50", "ACF(abs(returns), lag 50)"),
    ("corr_volume_abs_return", "corr(volume, abs(returns))"),
    ("tail_exceedance_ratio", "Tail ratio"),
)


@dataclass(frozen=True)
class BootstrapSummary:
    """Point estimate and bootstrap interval for one statistic."""

    key: str
    label: str
    point: float
    mean: float
    lower: float
    upper: float


@dataclass(frozen=True)
class BootstrapResult:
    """Result of a moving-block bootstrap."""

    summaries: tuple[BootstrapSummary, ...]
    n_resamples: int
    block_length: int
    seed: int


def block_indices(n: int, block_length: int, rng: np.random.Generator) -> np.ndarray:
    """Return ``n`` indices formed by contiguous blocks of ``block_length``."""
    if n < 1:
        raise ValueError("n must be positive")
    if block_length < 1 or block_length > n:
        raise ValueError("block_length must be between 1 and n")
    n_blocks = int(np.ceil(n / block_length))
    starts = rng.integers(0, n - block_length + 1, size=n_blocks)
    offsets = np.arange(block_length)
    indices = (starts[:, None] + offsets[None, :]).reshape(-1)[:n]
    return indices


def _metrics(returns: np.ndarray, volume: np.ndarray, tail_sigma: float) -> dict[str, float]:
    centred = returns - returns.mean()
    absolute = np.abs(centred)
    acf_returns = autocorrelation(returns, 50)
    acf_absolute = autocorrelation(absolute, 50)
    return {
        "kurtosis": kurtosis(returns),
        "acf_return_lag1": float(acf_returns[1]),
        "acf_abs_return_lag1": float(acf_absolute[1]),
        "acf_abs_return_lag50": float(acf_absolute[50]),
        "corr_volume_abs_return": correlation(volume, absolute),
        "tail_exceedance_ratio": tail_exceedance_ratio(returns, sigma=tail_sigma),
    }


def bootstrap_metrics(
    returns: Iterable[float],
    volume: Iterable[float],
    params: MetricsParams,
    n_resamples: int = 200,
    block_length: int = 1000,
    seed: int = 12345,
    confidence: float = 0.95,
) -> BootstrapResult:
    """Moving-block bootstrap for the six statistics in the fact table.

    Choose ``block_length`` well above the largest lag in the statistics.
    With contiguous blocks, the bootstrap autocorrelation at lag ``k`` is
    attenuated by roughly ``(block_length - k) / block_length``.
    """
    r = np.asarray(returns, dtype=float)
    v = np.asarray(volume, dtype=float)
    if r.ndim != 1 or v.ndim != 1 or r.size != v.size:
        raise ValueError("returns and volume must be one-dimensional and equally long")
    if r.size < 2 or not np.all(np.isfinite(r)) or not np.all(np.isfinite(v)):
        raise ValueError("returns and volume must be finite")
    if n_resamples < 1:
        raise ValueError("n_resamples must be positive")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    point = _metrics(r, v, params.tail_sigma)
    rng = np.random.default_rng(seed)
    samples: dict[str, list[float]] = {key: [] for key, _ in STATISTIC_KEYS}
    for _ in range(n_resamples):
        indices = block_indices(r.size, block_length, rng)
        resampled = _metrics(r[indices], v[indices], params.tail_sigma)
        for key in samples:
            samples[key].append(resampled[key])

    alpha = (1.0 - confidence) / 2.0
    summaries: list[BootstrapSummary] = []
    for key, label in STATISTIC_KEYS:
        values = np.asarray(samples[key], dtype=float)
        summaries.append(
            BootstrapSummary(
                key=key,
                label=label,
                point=float(point[key]),
                mean=float(values.mean()),
                lower=float(np.quantile(values, alpha)),
                upper=float(np.quantile(values, 1.0 - alpha)),
            )
        )
    return BootstrapResult(
        summaries=tuple(summaries),
        n_resamples=n_resamples,
        block_length=block_length,
        seed=seed,
    )


def format_bootstrap_markdown(result: BootstrapResult) -> str:
    """Render the bootstrap table as Markdown."""
    lines = [
        "| Statistic | Point estimate | Bootstrap mean | 95% interval |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in result.summaries:
        lines.append(
            f"| {item.label} | {item.point:.4g} | {item.mean:.4g} | "
            f"[{item.lower:.4g}, {item.upper:.4g}] |"
        )
    return "\n".join(lines)


def write_bootstrap_csv(result: BootstrapResult, path: str | Path) -> Path:
    """Write the bootstrap summary as a CSV file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["statistic", "point", "mean", "lower", "upper"])
        for item in result.summaries:
            writer.writerow(
                [
                    item.key,
                    f"{item.point:.10g}",
                    f"{item.mean:.10g}",
                    f"{item.lower:.10g}",
                    f"{item.upper:.10g}",
                ]
            )
    return output
