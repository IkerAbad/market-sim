from __future__ import annotations

import numpy as np
import pytest

from market_sim.config import MetricsParams
from market_sim.stylized import (
    all_facts_pass,
    autocorrelation,
    compute_metrics,
    evaluate_facts,
    format_markdown_table,
    kurtosis,
    tail_exceedance_ratio,
)


def test_autocorrelation_hand_built_series() -> None:
    values = np.array([1.0, 2.0, 3.0, 4.0])
    result = autocorrelation(values, max_lag=2)
    assert np.allclose(result, np.array([1.0, 0.25, -0.3]))


def test_autocorrelation_alternating_series() -> None:
    values = np.array([1.0, -1.0] * 50)
    result = autocorrelation(values, max_lag=2)
    assert result[0] == 1.0
    assert result[1] == pytest.approx(-0.99)
    assert result[2] == pytest.approx(0.98)


def test_autocorrelation_rejects_constant_series() -> None:
    with pytest.raises(ValueError):
        autocorrelation(np.ones(10), max_lag=2)


def test_autocorrelation_rejects_excessive_lag() -> None:
    with pytest.raises(ValueError):
        autocorrelation(np.arange(10.0), max_lag=10)


def test_kurtosis_hand_built_series() -> None:
    values = np.array([1.0, 2.0, 3.0, 4.0])
    assert kurtosis(values) == pytest.approx(1.64)


def test_kurtosis_two_point_series() -> None:
    values = np.array([-1.0, -1.0, 1.0, 1.0])
    assert kurtosis(values) == pytest.approx(1.0)


def test_kurtosis_of_normal_sample() -> None:
    rng = np.random.default_rng(42)
    values = rng.normal(size=100_000)
    assert kurtosis(values) == pytest.approx(3.0, abs=0.1)


def test_tail_ratio_of_normal_sample() -> None:
    rng = np.random.default_rng(43)
    values = rng.normal(size=200_000)
    ratio = tail_exceedance_ratio(values, sigma=4.0)
    assert 0.5 < ratio < 1.8


def test_tail_ratio_detects_fat_tails() -> None:
    rng = np.random.default_rng(44)
    values = rng.standard_t(df=3, size=100_000)
    assert tail_exceedance_ratio(values, sigma=4.0) > 3.0


def test_compute_metrics_keys_and_volume_correlation() -> None:
    rng = np.random.default_rng(45)
    returns = rng.normal(0.0, 0.01, size=1000)
    volume = np.abs(returns - returns.mean())
    metrics = compute_metrics(returns, volume, MetricsParams(acf_lags=50))
    assert metrics["n_observations"] == 1000
    assert metrics["kurtosis"] > 0
    assert abs(float(metrics["corr_volume_abs_return"]) - 1.0) < 1e-12
    assert metrics["acf_abs_return_lag50"] is not None
    assert metrics["acf_abs_return_lag200"] is None


def test_compute_metrics_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        compute_metrics(
            np.zeros(100),
            np.zeros(99),
            MetricsParams(acf_lags=50),
        )


def test_compute_metrics_rejects_constant_volume() -> None:
    rng = np.random.default_rng(46)
    with pytest.raises(ValueError):
        compute_metrics(
            rng.normal(size=1000),
            np.ones(1000),
            MetricsParams(acf_lags=50),
        )


def test_evaluate_facts_and_markdown() -> None:
    metrics = {
        "kurtosis": 5.0,
        "acf_return_lag1": 0.01,
        "acf_abs_return_lag1": 0.2,
        "acf_abs_return_lag50": 0.05,
        "corr_volume_abs_return": 0.4,
        "tail_exceedance_ratio": 10.0,
    }
    params = MetricsParams()
    rows = evaluate_facts(metrics, params)
    assert len(rows) == 6
    assert all_facts_pass(rows)
    table = format_markdown_table(rows)
    assert "| Fact | Statistic | Value | Criterion | Pass |" in table
    assert "Kurtosis" in table
    assert "yes" in table

    metrics["kurtosis"] = 2.0
    failing_rows = evaluate_facts(metrics, params)
    assert not all_facts_pass(failing_rows)
    assert failing_rows[0]["passes"] is False
