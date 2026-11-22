"""Multi-seed robustness analysis.

A single seed is one draw from the model.  This module runs the same
configuration over a set of seeds, computes the stylized-fact statistics for
each one and summarizes the distribution.  The pass rate across seeds is a
stronger statement than a single passing table.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, replace
from itertools import repeat
from pathlib import Path
from typing import Any

import numpy as np

from .config import SimulationConfig
from .market import simulate
from .stylized import all_facts_pass, compute_metrics, evaluate_facts

STATISTIC_KEYS: tuple[tuple[str, str], ...] = (
    ("kurtosis", "Kurtosis"),
    ("acf_return_lag1", "ACF(returns, lag 1)"),
    ("acf_abs_return_lag1", "ACF(abs(returns), lag 1)"),
    ("acf_abs_return_lag50", "ACF(abs(returns), lag 50)"),
    ("corr_volume_abs_return", "corr(volume, abs(returns))"),
    ("tail_exceedance_ratio", "Tail ratio"),
)


@dataclass(frozen=True)
class SeedResult:
    """Statistics and fact outcomes for one seed."""

    seed: int
    metrics: dict[str, float | int | None]
    facts: list[dict[str, Any]]
    all_pass: bool


@dataclass(frozen=True)
class StatisticSummary:
    """Distribution of one statistic across seeds."""

    key: str
    label: str
    mean: float
    median: float
    sd: float
    minimum: float
    maximum: float
    q05: float
    q95: float
    pass_count: int


@dataclass(frozen=True)
class EnsembleSummary:
    """Aggregate result of a multi-seed run."""

    n_seeds: int
    overall_pass_count: int
    statistics: tuple[StatisticSummary, ...]


def parse_seeds(spec: str) -> list[int]:
    """Parse ``"1-3,7,10-12"`` into a sorted list of unique seeds."""
    seeds: set[int] = set()
    for part in spec.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start < 0 or end < start:
                raise ValueError(f"invalid seed range: {token!r}")
            seeds.update(range(start, end + 1))
        else:
            value = int(token)
            if value < 0:
                raise ValueError(f"seeds must be non-negative: {token!r}")
            seeds.add(value)
    if not seeds:
        raise ValueError("at least one seed is required")
    return sorted(seeds)


def run_seed(config: SimulationConfig, seed: int) -> SeedResult:
    """Run one seed and evaluate its stylized facts."""
    seed_config = replace(config, seed=seed)
    result = simulate(seed_config)
    returns, volume = result.analysis_window()
    metrics = compute_metrics(returns, volume, config.metrics)
    facts = evaluate_facts(metrics, config.metrics)
    return SeedResult(
        seed=seed,
        metrics=metrics,
        facts=facts,
        all_pass=all_facts_pass(facts),
    )


def run_ensemble(config: SimulationConfig, seeds: Iterable[int], jobs: int = 1) -> list[SeedResult]:
    """Run a configuration over several seeds.

    ``jobs`` greater than one uses a process pool.  The result order follows
    the sorted seed order.
    """
    seed_list = sorted(set(seeds))
    if not seed_list:
        raise ValueError("at least one seed is required")
    if jobs <= 1 or len(seed_list) == 1:
        return [run_seed(config, seed) for seed in seed_list]
    workers = min(jobs, len(seed_list))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(run_seed, repeat(config), seed_list))


def _metric_value(result: SeedResult, key: str) -> float:
    value = result.metrics.get(key)
    if value is None:
        raise ValueError(f"metric {key!r} is missing for seed {result.seed}")
    return float(value)


def _fact_pass(result: SeedResult, index: int) -> bool:
    if index >= len(result.facts):
        raise IndexError(f"fact row {index} is missing for seed {result.seed}")
    return bool(result.facts[index]["passes"])


def summarize_ensemble(results: Sequence[SeedResult]) -> EnsembleSummary:
    """Summarize each statistic and the joint pass rate."""
    if not results:
        raise ValueError("at least one result is required")
    summaries: list[StatisticSummary] = []
    for index, (key, label) in enumerate(STATISTIC_KEYS):
        values = np.asarray([_metric_value(result, key) for result in results], dtype=float)
        pass_count = sum(_fact_pass(result, index) for result in results)
        sd = float(values.std(ddof=1)) if values.size > 1 else 0.0
        q05, q95 = np.quantile(values, [0.05, 0.95])
        summaries.append(
            StatisticSummary(
                key=key,
                label=label,
                mean=float(values.mean()),
                median=float(np.median(values)),
                sd=sd,
                minimum=float(values.min()),
                maximum=float(values.max()),
                q05=float(q05),
                q95=float(q95),
                pass_count=pass_count,
            )
        )
    return EnsembleSummary(
        n_seeds=len(results),
        overall_pass_count=sum(result.all_pass for result in results),
        statistics=tuple(summaries),
    )


def summary_to_dict(summary: EnsembleSummary) -> dict[str, Any]:
    """Convert the summary to a JSON-serialisable mapping."""
    return {
        "n_seeds": summary.n_seeds,
        "overall_pass_count": summary.overall_pass_count,
        "overall_pass_rate": summary.overall_pass_count / summary.n_seeds,
        "statistics": [asdict(item) for item in summary.statistics],
    }


def format_summary_markdown(summary: EnsembleSummary) -> str:
    """Render the multi-seed summary as a Markdown table."""
    lines = [
        "| Statistic | Mean | Median | SD | Min | Max | 5% | 95% | Seeds passing |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summary.statistics:
        lines.append(
            f"| {item.label} | {item.mean:.4g} | {item.median:.4g} | {item.sd:.3g} | "
            f"{item.minimum:.4g} | {item.maximum:.4g} | {item.q05:.4g} | "
            f"{item.q95:.4g} | {item.pass_count}/{summary.n_seeds} |"
        )
    return "\n".join(lines)


def write_ensemble_csv(results: Sequence[SeedResult], path: str | Path) -> Path:
    """Write one row per seed with all statistics and the joint outcome."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    header = ["seed", *(key for key, _ in STATISTIC_KEYS), "all_facts_pass"]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for result in results:
            values: list[str | int] = [result.seed]
            for key, _ in STATISTIC_KEYS:
                value = result.metrics.get(key)
                values.append("" if value is None else f"{float(value):.10g}")
            values.append(1 if result.all_pass else 0)
            writer.writerow(values)
    return output
