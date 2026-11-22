from __future__ import annotations

import csv

import numpy as np
import pytest

from market_sim.ablations import (
    ABLATIONS,
    Ablation,
    ablation_report,
    format_ablation_markdown,
    run_ablation_grid,
    run_ablation_point,
    summarize_ablations,
    write_ablation_csv,
)
from market_sim.config import MetricsParams, ModelParams, SimulationConfig


def make_config() -> SimulationConfig:
    return SimulationConfig(
        seed=1,
        n_steps=200,
        burn_in=20,
        model=ModelParams(n_agents=20, memory_min=2, memory_max=10),
        metrics=MetricsParams(acf_lags=50),
    )


def test_ablation_catalog() -> None:
    names = [ablation.name for ablation in ABLATIONS]
    assert names[0] == "baseline"
    assert "noise_only" in names
    assert "no_activity" in names
    assert len(names) == len(set(names))


def test_run_ablation_point() -> None:
    result = run_ablation_point(make_config(), ABLATIONS[0], seed=3)
    assert result.name == "baseline"
    assert result.seed == 3
    assert 0 <= result.pass_count <= 6
    assert len(result.passes) == 6
    assert set(result.metrics) == {
        "kurtosis",
        "acf_return_lag1",
        "acf_abs_return_lag1",
        "acf_abs_return_lag50",
        "corr_volume_abs_return",
        "tail_exceedance_ratio",
    }


def test_run_ablation_grid_and_summary() -> None:
    ablations = ABLATIONS[:3]
    results = run_ablation_grid(make_config(), ablations, [1, 2], jobs=1)
    assert len(results) == 6
    summary = summarize_ablations(results, ablations)
    assert summary.n_seeds == 2
    assert summary.pass_counts.shape == (3, 6)
    assert summary.mean_pass_count.shape == (3,)
    assert summary.all_pass_count.shape == (3,)
    assert np.all(summary.pass_counts >= 0)
    assert np.all(summary.pass_counts <= 2)
    table = format_ablation_markdown(summary)
    assert "| Ablation |" in table
    report = ablation_report(summary, "python scripts/run_ablations.py")
    assert "# Ablation study" in report


def test_run_ablation_grid_rejects_empty_seeds() -> None:
    with pytest.raises(ValueError):
        run_ablation_grid(make_config(), ABLATIONS[:1], [], jobs=1)


def test_summarize_rejects_empty_results() -> None:
    with pytest.raises(ValueError):
        summarize_ablations([], ABLATIONS[:1])


def test_write_ablation_csv(tmp_path) -> None:
    results = run_ablation_grid(make_config(), ABLATIONS[:1], [1], jobs=1)
    path = write_ablation_csv(results, tmp_path / "ablations.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert set(rows[0]) == {
        "ablation",
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


def test_custom_ablation() -> None:
    custom = Ablation("custom", "custom variant", {"activity_sigma": 0.0})
    result = run_ablation_point(make_config(), custom, seed=1)
    assert result.name == "custom"
