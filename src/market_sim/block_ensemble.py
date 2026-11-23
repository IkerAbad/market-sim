"""Block stability of the six statistics across several seeds.

The single-run block table shows that one baseline series is stable inside its
own window.  This module repeats the block analysis over a set of seeds and
counts how often each statistic passes its criterion in each block.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from functools import partial
from pathlib import Path

from .config import MetricsParams, SimulationConfig
from .market import simulate
from .stability import (
    METRIC_KEYS,
    METRIC_LABELS,
    BlockMetrics,
    block_metrics,
    block_passes,
)


@dataclass(frozen=True)
class BlockSeedResult:
    """Block statistics for one seed."""

    seed: int
    blocks: tuple[BlockMetrics, ...]


@dataclass(frozen=True)
class StatisticBlockRate:
    """Block pass count for one statistic."""

    key: str
    label: str
    passes: int
    total: int

    @property
    def rate(self) -> float:
        return self.passes / self.total


@dataclass(frozen=True)
class BlockEnsembleSummary:
    """Aggregate block result over a set of seeds."""

    n_seeds: int
    n_blocks: int
    statistics: tuple[StatisticBlockRate, ...]
    seed_all_blocks: int


def run_block_seed(config: SimulationConfig, seed: int, n_blocks: int = 10) -> BlockSeedResult:
    """Run one seed and compute the six statistics in each block."""
    result = simulate(replace(config, seed=seed))
    returns, volume = result.analysis_window()
    blocks = block_metrics(returns, volume, config.metrics, n_blocks=n_blocks)
    return BlockSeedResult(seed=seed, blocks=tuple(blocks))


def run_block_ensemble(
    config: SimulationConfig,
    seeds: Iterable[int],
    n_blocks: int = 10,
    jobs: int = 1,
) -> list[BlockSeedResult]:
    """Run the block analysis over several seeds."""
    seed_list = sorted(set(seeds))
    if not seed_list:
        raise ValueError("at least one seed is required")
    if jobs <= 1 or len(seed_list) == 1:
        return [run_block_seed(config, seed, n_blocks) for seed in seed_list]
    workers = min(jobs, len(seed_list))
    worker = partial(run_block_seed, config, n_blocks=n_blocks)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(worker, seed_list))


def _block_pass_count(block: BlockMetrics, params: MetricsParams) -> int:
    return sum(block_passes(key, block.metrics[key], params) for key in METRIC_KEYS)


def summarize_block_ensemble(
    results: Sequence[BlockSeedResult], params: MetricsParams
) -> BlockEnsembleSummary:
    """Count per-statistic and per-seed block passes."""
    if not results:
        raise ValueError("at least one result is required")
    n_blocks = len(results[0].blocks)
    if any(len(result.blocks) != n_blocks for result in results):
        raise ValueError("every seed must have the same number of blocks")
    statistics = tuple(
        StatisticBlockRate(
            key=key,
            label=METRIC_LABELS[key],
            passes=sum(
                block_passes(key, block.metrics[key], params)
                for result in results
                for block in result.blocks
            ),
            total=len(results) * n_blocks,
        )
        for key in METRIC_KEYS
    )
    seed_all_blocks = sum(
        all(
            block_passes(key, block.metrics[key], params)
            for block in result.blocks
            for key in METRIC_KEYS
        )
        for result in results
    )
    return BlockEnsembleSummary(
        n_seeds=len(results),
        n_blocks=n_blocks,
        statistics=statistics,
        seed_all_blocks=seed_all_blocks,
    )


def format_block_ensemble_markdown(
    results: Sequence[BlockSeedResult],
    params: MetricsParams,
) -> str:
    """Render the per-seed and per-statistic tables as Markdown."""
    summary = summarize_block_ensemble(results, params)
    seed_lines = [
        "| Seed | Blocks passing all six | All blocks |",
        "| ---: | ---: | :---: |",
    ]
    for result in results:
        counts = [_block_pass_count(block, params) for block in result.blocks]
        passing = sum(count == len(METRIC_KEYS) for count in counts)
        seed_lines.append(
            f"| {result.seed} | {passing}/{len(counts)} | "
            f"{'yes' if passing == len(counts) else 'no'} |"
        )
    statistic_lines = [
        "| Statistic | Blocks passing | Rate |",
        "| --- | ---: | ---: |",
    ]
    for item in summary.statistics:
        statistic_lines.append(
            f"| {item.label} | {item.passes}/{item.total} | {100.0 * item.rate:.1f}% |"
        )
    return "\n".join([*seed_lines, "", *statistic_lines])


def write_block_ensemble_csv(
    results: Sequence[BlockSeedResult],
    params: MetricsParams,
    path: str | Path,
) -> Path:
    """Write one row per seed and block."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "seed",
        "block",
        "start",
        "end",
        "n_observations",
        *METRIC_KEYS,
        "block_pass_count",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for result in results:
            for block in result.blocks:
                writer.writerow(
                    [
                        result.seed,
                        block.index,
                        block.start,
                        block.end,
                        block.n_observations,
                        *(f"{block.metrics[key]:.10g}" for key in METRIC_KEYS),
                        _block_pass_count(block, params),
                    ]
                )
    return output
