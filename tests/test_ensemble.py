from __future__ import annotations

import csv

import pytest

from market_sim.config import MetricsParams, ModelParams, SimulationConfig
from market_sim.ensemble import (
    STATISTIC_KEYS,
    SeedResult,
    format_summary_markdown,
    parse_seeds,
    run_ensemble,
    summarize_ensemble,
    summary_to_dict,
    wilson_interval,
    write_ensemble_csv,
)


def make_config() -> SimulationConfig:
    return SimulationConfig(
        seed=1,
        n_steps=300,
        burn_in=20,
        model=ModelParams(
            n_agents=20,
            memory_min=2,
            memory_max=10,
            activity_sigma=0.5,
        ),
        metrics=MetricsParams(acf_lags=50),
    )


def test_parse_seeds() -> None:
    assert parse_seeds("1-3,7") == [1, 2, 3, 7]
    assert parse_seeds("5, 5, 2-3") == [2, 3, 5]
    assert parse_seeds("0") == [0]


def test_parse_seeds_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        parse_seeds("")
    with pytest.raises(ValueError):
        parse_seeds("3-1")
    with pytest.raises(ValueError):
        parse_seeds("-1")


def test_wilson_interval() -> None:
    lower, upper = wilson_interval(5, 10)
    assert 0.0 < lower < 0.5 < upper < 1.0
    lower, upper = wilson_interval(10, 10)
    assert lower < 1.0
    assert upper == 1.0
    lower, upper = wilson_interval(0, 10)
    assert lower == 0.0
    assert upper > 0.0
    with pytest.raises(ValueError):
        wilson_interval(0, 0)
    with pytest.raises(ValueError):
        wilson_interval(11, 10)


def test_run_ensemble() -> None:
    results = run_ensemble(make_config(), [1, 2], jobs=1)
    assert [result.seed for result in results] == [1, 2]
    assert all(isinstance(result.all_pass, bool) for result in results)
    assert all(result.metrics["kurtosis"] is not None for result in results)
    assert all(len(result.facts) == 6 for result in results)


def test_summarize_ensemble() -> None:
    results = run_ensemble(make_config(), [1, 2], jobs=1)
    summary = summarize_ensemble(results)
    assert summary.n_seeds == 2
    assert len(summary.statistics) == 6
    assert 0 <= summary.overall_pass_count <= 2
    assert all(0 <= item.pass_count <= 2 for item in summary.statistics)
    payload = summary_to_dict(summary)
    assert payload["n_seeds"] == 2
    assert 0.0 <= float(payload["overall_pass_rate"]) <= 1.0


def test_format_summary_markdown() -> None:
    summary = summarize_ensemble(run_ensemble(make_config(), [1, 2], jobs=1))
    table = format_summary_markdown(summary)
    assert "| Statistic | Mean | Median | SD | Min | Max | 5% | 95% | Seeds passing |" in table
    assert "Kurtosis" in table


def test_write_ensemble_csv(tmp_path) -> None:
    results = run_ensemble(make_config(), [1, 2], jobs=1)
    path = write_ensemble_csv(results, tmp_path / "metrics.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert set(rows[0]) == {
        "seed",
        "kurtosis",
        "acf_return_lag1",
        "acf_abs_return_lag1",
        "acf_abs_return_lag50",
        "corr_volume_abs_return",
        "tail_exceedance_ratio",
        "all_facts_pass",
    }


def test_run_ensemble_uses_process_pool(monkeypatch) -> None:
    class FakeExecutor:
        def __init__(self, max_workers: int) -> None:
            self.max_workers = max_workers

        def __enter__(self) -> FakeExecutor:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def map(self, function, *iterables):
            return map(function, *iterables)

    monkeypatch.setattr("market_sim.ensemble.ProcessPoolExecutor", FakeExecutor)
    results = run_ensemble(make_config(), [3, 4], jobs=2)
    assert [result.seed for result in results] == [3, 4]


def test_run_ensemble_rejects_empty_seed_list() -> None:
    with pytest.raises(ValueError):
        run_ensemble(make_config(), [], jobs=1)


def test_summarize_ensemble_rejects_empty_results() -> None:
    with pytest.raises(ValueError):
        summarize_ensemble([])


def test_summarize_ensemble_rejects_missing_metric() -> None:
    result = SeedResult(seed=1, metrics={}, facts=[], all_pass=False)
    with pytest.raises(ValueError):
        summarize_ensemble([result])


def test_summarize_ensemble_rejects_missing_fact_row() -> None:
    metrics = {key: 1.0 for key, _ in STATISTIC_KEYS}
    result = SeedResult(seed=1, metrics=metrics, facts=[], all_pass=False)
    with pytest.raises(IndexError):
        summarize_ensemble([result])
