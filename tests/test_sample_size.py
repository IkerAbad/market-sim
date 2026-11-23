from __future__ import annotations

import csv

import numpy as np
import pytest

from market_sim.config import MetricsParams, ModelParams, SimulationConfig
from market_sim.sample_size import (
    format_sample_size_markdown,
    run_sample_size_grid,
    run_sample_size_point,
    sample_size_report,
    summarize_sample_size,
    write_sample_size_csv,
)


def make_config() -> SimulationConfig:
    return SimulationConfig(
        seed=1,
        n_steps=100,
        burn_in=20,
        model=ModelParams(n_agents=20, memory_min=2, memory_max=10),
        metrics=MetricsParams(acf_lags=50),
    )


def test_run_sample_size_point() -> None:
    point = run_sample_size_point(make_config(), size=2000, seed=3)
    assert point.size == 2000
    assert point.seed == 3
    assert 0 <= point.pass_count <= 6
    assert len(point.passes) == 6
    assert set(point.metrics) == {
        "kurtosis",
        "acf_return_lag1",
        "acf_abs_return_lag1",
        "acf_abs_return_lag50",
        "corr_volume_abs_return",
        "tail_exceedance_ratio",
    }


def test_run_sample_size_grid_and_summary() -> None:
    results = run_sample_size_grid(make_config(), [2000, 4000], [1, 2], jobs=1)
    assert len(results) == 4
    summary = summarize_sample_size(results)
    assert summary.sizes == (2000, 4000)
    assert summary.n_seeds == 2
    assert summary.pass_counts.shape == (2, 6)
    assert summary.all_pass_count.shape == (2,)
    assert set(summary.mean_metrics) == {
        "kurtosis",
        "acf_return_lag1",
        "acf_abs_return_lag1",
        "acf_abs_return_lag50",
        "corr_volume_abs_return",
        "tail_exceedance_ratio",
    }
    table = format_sample_size_markdown(summary)
    assert "| Size | Seeds |" in table
    report = sample_size_report(summary, "python scripts/run_sample_size.py")
    assert "# Sample-size sensitivity" in report


def test_sample_size_rejects_empty_inputs() -> None:
    with pytest.raises(ValueError):
        run_sample_size_grid(make_config(), [], [1], jobs=1)
    with pytest.raises(ValueError):
        run_sample_size_grid(make_config(), [2000], [], jobs=1)
    with pytest.raises(ValueError):
        run_sample_size_point(make_config(), size=1, seed=1)


def test_summarize_rejects_empty_results() -> None:
    with pytest.raises(ValueError):
        summarize_sample_size([])


def test_write_sample_size_csv(tmp_path) -> None:
    results = run_sample_size_grid(make_config(), [2000], [1], jobs=1)
    path = write_sample_size_csv(results, tmp_path / "sample_size.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert set(rows[0]) == {
        "size",
        "seed",
        "pass_count",
        "all_pass",
        "kurtosis",
        "acf_return_lag1",
        "acf_abs_return_lag1",
        "acf_abs_return_lag50",
        "corr_volume_abs_return",
        "tail_exceedance_ratio",
    }
    assert np.isfinite(float(rows[0]["kurtosis"]))
