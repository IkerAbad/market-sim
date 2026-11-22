from __future__ import annotations

import csv

import numpy as np
import pytest

from market_sim.benchmarks import (
    benchmark_metrics,
    evaluate_benchmark,
    format_benchmark_markdown,
    garch11_returns,
    gaussian_returns,
    student_t_returns,
    write_benchmark_csv,
)
from market_sim.config import MetricsParams


def test_gaussian_returns() -> None:
    first = gaussian_returns(1000, seed=1)
    second = gaussian_returns(1000, seed=1)
    assert first.shape == (1000,)
    assert np.array_equal(first, second)
    with pytest.raises(ValueError):
        gaussian_returns(0)


def test_student_t_returns() -> None:
    values = student_t_returns(1000, df=5.0, seed=2)
    assert values.shape == (1000,)
    assert np.all(np.isfinite(values))
    with pytest.raises(ValueError):
        student_t_returns(100, df=2.0)


def test_garch11_returns() -> None:
    first = garch11_returns(1000, seed=3)
    second = garch11_returns(1000, seed=3)
    assert first.shape == (1000,)
    assert np.all(np.isfinite(first))
    assert np.array_equal(first, second)
    with pytest.raises(ValueError):
        garch11_returns(100, alpha=0.5, beta=0.6)
    with pytest.raises(ValueError):
        garch11_returns(100, omega=0.0)


def test_benchmark_metrics_and_evaluation() -> None:
    params = MetricsParams(acf_lags=200)
    values = garch11_returns(1000, seed=3)
    metrics = benchmark_metrics(values, params)
    assert set(metrics) == {
        "kurtosis",
        "acf_return_lag1",
        "acf_abs_return_lag1",
        "acf_abs_return_lag50",
        "tail_exceedance_ratio",
    }
    point = evaluate_benchmark("garch", "test", metrics, params)
    assert 0 <= point.pass_count <= 5
    assert len(point.passes) == 5


def test_benchmark_table_and_csv(tmp_path) -> None:
    params = MetricsParams(acf_lags=200)
    points = [
        evaluate_benchmark(
            name,
            name,
            benchmark_metrics(series, params),
            params,
        )
        for name, series in (
            ("gaussian", gaussian_returns(1000, seed=1)),
            ("garch", garch11_returns(1000, seed=3)),
        )
    ]
    table = format_benchmark_markdown(points)
    assert "| Series | Kurtosis |" in table
    path = write_benchmark_csv(points, tmp_path / "benchmarks.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert set(rows[0]) == {
        "series",
        "kurtosis",
        "acf_return_lag1",
        "acf_abs_return_lag1",
        "acf_abs_return_lag50",
        "tail_exceedance_ratio",
        "pass_count",
    }
