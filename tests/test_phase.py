from __future__ import annotations

import csv

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest

from market_sim.config import MetricsParams, ModelParams, SimulationConfig
from market_sim.phase import (
    PhasePoint,
    format_phase_markdown,
    parse_values,
    phase_report,
    plot_phase_heatmap,
    run_phase_grid,
    run_phase_point,
    summarize_phase,
    write_phase_csv,
)


def make_config() -> SimulationConfig:
    return SimulationConfig(
        seed=1,
        n_steps=200,
        burn_in=20,
        model=ModelParams(n_agents=20, memory_min=2, memory_max=10),
        metrics=MetricsParams(acf_lags=50),
    )


def test_parse_values() -> None:
    assert parse_values("0.5, 1.0,1.25") == (0.5, 1.0, 1.25)
    with pytest.raises(ValueError):
        parse_values("")
    with pytest.raises(ValueError):
        parse_values("-1")
    with pytest.raises(ValueError):
        parse_values("nan")


def test_run_phase_point() -> None:
    point = run_phase_point(make_config(), 1.0, 0.1, seed=3)
    assert point.activity_sigma == 1.0
    assert point.max_chartist_demand == 0.1
    assert point.seed == 3
    assert 0 <= point.pass_count <= 6
    assert isinstance(point.all_pass, bool)
    assert "kurtosis" in point.metrics


def test_run_phase_grid_and_summary() -> None:
    points = run_phase_grid(make_config(), [0.5, 1.0], [0.05, 0.1], [1, 2], jobs=1)
    assert len(points) == 8
    summary = summarize_phase(points)
    assert summary.mean_pass.shape == (2, 2)
    assert summary.all_pass_count.shape == (2, 2)
    assert summary.n_seeds == 2
    assert np.all(summary.mean_pass >= 0)
    assert np.all(summary.mean_pass <= 6)
    table = format_phase_markdown(summary)
    assert "max_chartist_demand" in table
    assert "activity_sigma" in table
    report = phase_report(summary, "python scripts/run_phase_diagram.py")
    assert "# Parameter robustness map" in report


def test_run_phase_grid_rejects_empty_seeds() -> None:
    with pytest.raises(ValueError):
        run_phase_grid(make_config(), [1.0], [0.1], [], jobs=1)


def test_run_phase_grid_uses_process_pool(monkeypatch) -> None:
    class FakeFuture:
        def __init__(self, value: PhasePoint) -> None:
            self.value = value

        def result(self) -> PhasePoint:
            return self.value

    class FakeExecutor:
        def __init__(self, max_workers: int) -> None:
            self.max_workers = max_workers

        def __enter__(self) -> FakeExecutor:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def submit(self, function, *args):
            return FakeFuture(function(*args))

    monkeypatch.setattr("market_sim.phase.ProcessPoolExecutor", FakeExecutor)
    points = run_phase_grid(make_config(), [0.5, 1.0], [0.1], [1, 2], jobs=2)
    assert len(points) == 4
    assert {point.seed for point in points} == {1, 2}


def test_summarize_phase_rejects_incomplete_grid() -> None:
    points = [
        PhasePoint(1.0, 0.1, 1, 6, True, {}),
        PhasePoint(1.0, 0.2, 1, 6, True, {}),
        PhasePoint(0.5, 0.1, 1, 6, True, {}),
    ]
    with pytest.raises(ValueError):
        summarize_phase(points)


def test_summarize_phase_rejects_uneven_seed_counts() -> None:
    metrics = {
        "kurtosis": 5.0,
        "acf_return_lag1": 0.0,
        "acf_abs_return_lag1": 0.2,
        "acf_abs_return_lag50": 0.1,
        "corr_volume_abs_return": 0.5,
        "tail_exceedance_ratio": 10.0,
    }
    points = [
        PhasePoint(1.0, 0.1, 1, 6, True, metrics),
        PhasePoint(1.0, 0.1, 2, 6, True, metrics),
        PhasePoint(1.0, 0.2, 1, 6, True, metrics),
    ]
    with pytest.raises(ValueError):
        summarize_phase(points)


def test_write_phase_csv(tmp_path) -> None:
    points = run_phase_grid(make_config(), [1.0], [0.1], [1], jobs=1)
    path = write_phase_csv(points, tmp_path / "phase.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert set(rows[0]) == {
        "activity_sigma",
        "max_chartist_demand",
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


def test_plot_phase_heatmap(tmp_path) -> None:
    points = run_phase_grid(make_config(), [0.5, 1.0], [0.1, 0.2], [1], jobs=1)
    summary = summarize_phase(points)
    path = plot_phase_heatmap(summary, tmp_path / "phase.png")
    assert path.exists()
    assert path.stat().st_size > 1000
