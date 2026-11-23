from __future__ import annotations

import csv

import pytest

from market_sim.block_ensemble import (
    BlockSeedResult,
    format_block_ensemble_markdown,
    run_block_ensemble,
    run_block_seed,
    summarize_block_ensemble,
    write_block_ensemble_csv,
)
from market_sim.config import MetricsParams, ModelParams, SimulationConfig
from market_sim.stability import METRIC_KEYS

PARAMS = MetricsParams(acf_lags=50)


def make_config() -> SimulationConfig:
    return SimulationConfig(
        seed=1,
        n_steps=5000,
        burn_in=20,
        model=ModelParams(
            n_agents=20,
            memory_min=2,
            memory_max=10,
            activity_sigma=0.5,
        ),
        metrics=PARAMS,
    )


def test_run_block_seed() -> None:
    result = run_block_seed(make_config(), seed=3, n_blocks=5)
    assert result.seed == 3
    assert len(result.blocks) == 5
    assert sum(block.n_observations for block in result.blocks) == 4980
    assert all(set(block.metrics) == set(METRIC_KEYS) for block in result.blocks)


def test_run_block_ensemble_serial_and_parallel() -> None:
    config = make_config()
    serial = run_block_ensemble(config, [1, 2], n_blocks=5, jobs=1)
    parallel = run_block_ensemble(config, [1, 2], n_blocks=5, jobs=2)
    assert [result.seed for result in serial] == [1, 2]
    assert [result.seed for result in parallel] == [1, 2]
    assert len(serial[0].blocks) == 5
    assert len(parallel[0].blocks) == 5


def test_empty_seeds_are_rejected() -> None:
    with pytest.raises(ValueError):
        run_block_ensemble(make_config(), [], n_blocks=5)


def test_summary_counts() -> None:
    results = run_block_ensemble(make_config(), [1, 2], n_blocks=5, jobs=1)
    summary = summarize_block_ensemble(results, PARAMS)
    assert summary.n_seeds == 2
    assert summary.n_blocks == 5
    assert len(summary.statistics) == len(METRIC_KEYS)
    assert all(item.total == 10 for item in summary.statistics)
    assert 0 <= summary.seed_all_blocks <= 2


def test_summary_rejects_mismatched_blocks() -> None:
    result = run_block_seed(make_config(), seed=1, n_blocks=5)
    broken = BlockSeedResult(seed=2, blocks=result.blocks[:3])
    with pytest.raises(ValueError):
        summarize_block_ensemble([result, broken], PARAMS)


def test_summary_rejects_empty_results() -> None:
    with pytest.raises(ValueError):
        summarize_block_ensemble([], PARAMS)


def test_markdown_and_csv(tmp_path) -> None:
    results = run_block_ensemble(make_config(), [1, 2], n_blocks=5, jobs=1)
    markdown = format_block_ensemble_markdown(results, PARAMS)
    assert "| Seed | Blocks passing all six | All blocks |" in markdown
    assert "| Statistic | Blocks passing | Rate |" in markdown
    path = write_block_ensemble_csv(results, PARAMS, tmp_path / "blocks.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 10
    assert rows[0]["seed"] == "1"
    assert rows[0]["block"] == "1"
