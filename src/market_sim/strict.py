"""Evaluate the per-seed hold-out under stricter tail criteria.

The main table uses kurtosis above 3 and tail ratio above 1.  Those two
thresholds are weak: Gaussian samples pass them about half of the time.  This
module recomputes the five price facts with kurtosis above 5 and tail ratio
above 10, and reports which seeds fail.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .benchmark_rates import FACT_KEYS
from .benchmarks import evaluate_benchmark
from .config import MetricsParams
from .ensemble import wilson_interval

STRICT_KURTOSIS = 5.0
STRICT_TAIL_RATIO = 10.0


@dataclass(frozen=True)
class StrictFact:
    """Pass count and Wilson interval for one fact."""

    key: str
    label: str
    criterion: str
    passes: int
    total: int
    lower: float
    upper: float

    @property
    def rate(self) -> float:
        return self.passes / self.total


@dataclass(frozen=True)
class StrictFailure:
    """One seed that fails at least one strict fact."""

    seed: int
    failing: tuple[str, ...]
    metrics: dict[str, float]


@dataclass(frozen=True)
class StrictSummary:
    """Strict result for a set of seeds."""

    n_seeds: int
    facts: tuple[StrictFact, ...]
    all_pass: int
    all_lower: float
    all_upper: float
    failures: tuple[StrictFailure, ...]


def load_seed_metrics(path: str | Path) -> list[dict[str, float]]:
    """Load the seed and the five price metrics from an ensemble CSV."""
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("the CSV file has no header")
        required = ["seed", *(key for key, _ in FACT_KEYS)]
        missing = [name for name in required if name not in reader.fieldnames]
        if missing:
            raise ValueError(f"missing columns: {', '.join(missing)}")
        rows = [
            {
                "seed": float(raw["seed"]),
                **{key: float(raw[key]) for key, _ in FACT_KEYS},
            }
            for raw in reader
        ]
    if not rows:
        raise ValueError("the CSV file has no data rows")
    return rows


def _criteria(params: MetricsParams) -> dict[str, str]:
    return {
        "kurtosis": f"> {params.kurtosis_threshold:g}",
        "acf_return_lag1": f"abs(value) < {params.return_acf_threshold:g}",
        "acf_abs_return_lag1": f"> {params.abs_acf_lag1_threshold:g}",
        "acf_abs_return_lag50": f"> {params.abs_acf_lag50_threshold:g}",
        "tail_exceedance_ratio": f"> {params.tail_ratio_threshold:g}",
    }


def evaluate_strict(rows: Sequence[dict[str, float]], params: MetricsParams) -> StrictSummary:
    """Count strict passes and collect the failing seeds."""
    if not rows:
        raise ValueError("at least one seed is required")
    criteria = _criteria(params)
    counts = [0] * len(FACT_KEYS)
    all_pass = 0
    failures: list[StrictFailure] = []
    for row in rows:
        metrics = {key: float(row[key]) for key, _ in FACT_KEYS}
        point = evaluate_benchmark("model", "", metrics, params)
        for index, passed in enumerate(point.passes):
            counts[index] += int(passed)
        if point.pass_count == len(FACT_KEYS):
            all_pass += 1
        else:
            failing = tuple(
                label
                for (_, label), passed in zip(FACT_KEYS, point.passes, strict=True)
                if not passed
            )
            failures.append(
                StrictFailure(
                    seed=int(row["seed"]),
                    failing=failing,
                    metrics=metrics,
                )
            )
    facts = tuple(
        StrictFact(
            key=key,
            label=label,
            criterion=criteria[key],
            passes=counts[index],
            total=len(rows),
            lower=wilson_interval(counts[index], len(rows))[0],
            upper=wilson_interval(counts[index], len(rows))[1],
        )
        for index, (key, label) in enumerate(FACT_KEYS)
    )
    lower, upper = wilson_interval(all_pass, len(rows))
    return StrictSummary(
        n_seeds=len(rows),
        facts=facts,
        all_pass=all_pass,
        all_lower=lower,
        all_upper=upper,
        failures=tuple(failures),
    )


def format_strict_markdown(summary: StrictSummary) -> str:
    """Render the strict summary and the failing seeds as Markdown."""
    lines = [
        "| Fact | Criterion | Passes | 95% CI |",
        "| --- | --- | ---: | ---: |",
    ]
    for fact in summary.facts:
        lines.append(
            f"| {fact.label} | {fact.criterion} | {fact.passes}/{fact.total} | "
            f"[{fact.lower:.3f}, {fact.upper:.3f}] |"
        )
    lines.append(
        f"| All five | - | {summary.all_pass}/{summary.n_seeds} | "
        f"[{summary.all_lower:.3f}, {summary.all_upper:.3f}] |"
    )
    if summary.failures:
        lines.extend(
            [
                "",
                "| Seed | Failing facts | Kurtosis | Tail ratio |",
                "| ---: | --- | ---: | ---: |",
            ]
        )
        for failure in summary.failures:
            lines.append(
                f"| {failure.seed} | {', '.join(failure.failing)} | "
                f"{failure.metrics['kurtosis']:.4g} | "
                f"{failure.metrics['tail_exceedance_ratio']:.4g} |"
            )
    else:
        lines.extend(["", "No seed fails the strict criteria."])
    return "\n".join(lines)


def write_strict_csv(
    rows: Sequence[dict[str, float]], params: MetricsParams, path: str | Path
) -> Path:
    """Write one row per seed with the strict pass flags."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    header = ["seed", *(key for key, _ in FACT_KEYS), "pass_count", "all_pass"]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            metrics = {key: float(row[key]) for key, _ in FACT_KEYS}
            point = evaluate_benchmark("model", "", metrics, params)
            writer.writerow(
                [
                    int(row["seed"]),
                    *(1 if passed else 0 for passed in point.passes),
                    point.pass_count,
                    1 if point.pass_count == len(FACT_KEYS) else 0,
                ]
            )
    return output
