from __future__ import annotations

import csv

import numpy as np
import pytest

from market_sim.extra_facts import (
    additional_metrics,
    aggregational_kurtosis,
    dfa_hurst,
    evaluate_additional_facts,
    format_additional_table,
    format_aggregational_table,
    gain_loss_asymmetry,
    leverage_effect,
    leverage_profile,
    volume_volatility_lead_lag,
    write_additional_csv,
)


def leverage_series(n: int = 5000) -> np.ndarray:
    rng = np.random.default_rng(1)
    returns = np.zeros(n)
    volatility = np.ones(n) * 0.01
    shocks = rng.normal(size=n)
    for t in range(1, n):
        volatility[t] = (
            0.005 + 0.8 * volatility[t - 1] + 0.15 * abs(returns[t - 1]) - 0.1 * returns[t - 1]
        )
        returns[t] = volatility[t] * shocks[t]
    return returns


def test_leverage_effect_is_negative() -> None:
    returns = leverage_series()
    assert leverage_effect(returns, lag=1) < 0


def test_leverage_profile() -> None:
    returns = leverage_series()
    profile = leverage_profile(returns, max_lag=5)
    assert profile.shape == (5,)
    assert np.all(np.isfinite(profile))


def test_leverage_rejects_constant_series() -> None:
    with pytest.raises(ValueError):
        leverage_effect(np.ones(100))
    with pytest.raises(ValueError):
        leverage_effect(np.arange(100.0), lag=100)


def test_leverage_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        leverage_effect(np.ones((10, 2)))
    values = np.arange(100.0)
    values[0] = np.nan
    with pytest.raises(ValueError):
        leverage_effect(values)
    with pytest.raises(ValueError):
        leverage_profile(np.arange(100.0), max_lag=0)


def test_gain_loss_asymmetry_detects_larger_losses() -> None:
    returns = np.array([-3.0, -2.0, -1.0, -0.5, 0.5, 0.4, 0.3, 0.2])
    result = gain_loss_asymmetry(returns)
    assert float(result["volatility_ratio"]) > 1.0
    assert result["negative_count"] == 4
    assert result["positive_count"] == 4


def test_gain_loss_asymmetry_symmetric_series() -> None:
    returns = np.array([-1.0, 1.0, -2.0, 2.0, -3.0, 3.0])
    result = gain_loss_asymmetry(returns)
    assert float(result["volatility_ratio"]) == pytest.approx(1.0)


def test_gain_loss_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        gain_loss_asymmetry(np.ones((10, 2)))
    with pytest.raises(ValueError):
        gain_loss_asymmetry(np.array([1.0, 2.0, 3.0, 4.0]))
    values = np.arange(10.0)
    values[0] = np.inf
    with pytest.raises(ValueError):
        gain_loss_asymmetry(values)


def test_dfa_of_white_noise() -> None:
    rng = np.random.default_rng(3)
    exponent = dfa_hurst(rng.normal(size=10000))
    assert exponent == pytest.approx(0.5, abs=0.1)


def test_dfa_rejects_invalid_series() -> None:
    with pytest.raises(ValueError):
        dfa_hurst(np.ones(10000))
    with pytest.raises(ValueError):
        dfa_hurst(np.arange(10.0))
    with pytest.raises(ValueError):
        dfa_hurst(np.arange(100.0), scales=[1, 2, 3])
    with pytest.raises(ValueError):
        dfa_hurst(np.arange(100.0), scales=[8])
    with pytest.raises(ValueError):
        dfa_hurst(np.arange(32.0))
    values = np.arange(100.0)
    values[0] = np.nan
    with pytest.raises(ValueError):
        dfa_hurst(values)


def test_volume_leads_volatility() -> None:
    rng = np.random.default_rng(4)
    returns = rng.normal(size=5000)
    volume = np.empty_like(returns)
    volume[:-1] = np.abs(returns[1:]) + 0.1 * rng.normal(size=returns.size - 1)
    volume[-1] = 0.0
    best_lag, best_corr, profile = volume_volatility_lead_lag(returns, volume, max_lag=5)
    assert best_lag == 1
    assert best_corr > 0.5
    assert profile[1] > profile[0]


def test_volume_lead_lag_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        volume_volatility_lead_lag(np.arange(100.0), np.arange(99.0))
    values = np.arange(100.0)
    values[0] = np.nan
    with pytest.raises(ValueError):
        volume_volatility_lead_lag(values, np.arange(100.0))
    with pytest.raises(ValueError):
        volume_volatility_lead_lag(np.arange(100.0), np.arange(100.0), max_lag=-1)
    with pytest.raises(ValueError):
        volume_volatility_lead_lag(np.arange(100.0), np.arange(100.0), max_lag=100)
    with pytest.raises(ValueError):
        volume_volatility_lead_lag(np.ones(100), np.ones(100))


def test_additional_metrics_keys() -> None:
    returns = leverage_series()
    rng = np.random.default_rng(5)
    volume = np.abs(returns) + 0.1 * rng.normal(size=returns.size)
    metrics = additional_metrics(returns, volume)
    assert set(metrics) == {
        "leverage_lag1",
        "leverage_mean_1_10",
        "gain_loss_volatility_ratio",
        "gain_loss_mean_abs_ratio",
        "dfa_hurst_abs",
        "volume_volatility_best_lag",
        "volume_volatility_best_corr",
        "kurtosis_h1",
        "kurtosis_h5",
        "kurtosis_h20",
        "kurtosis_h60",
    }
    assert all(np.isfinite(float(value)) for value in metrics.values())


def test_aggregational_kurtosis() -> None:
    rng = np.random.default_rng(9)
    returns = rng.standard_t(df=4, size=10000)
    values = aggregational_kurtosis(returns)
    assert set(values) == {1, 5, 20, 60}
    assert values[1] > values[60]
    with pytest.raises(ValueError):
        aggregational_kurtosis(returns, horizons=(0,))
    with pytest.raises(ValueError):
        aggregational_kurtosis(np.array([1.0, 2.0, 3.0, 4.0]), horizons=(2,))
    with pytest.raises(ValueError):
        aggregational_kurtosis(np.array([1.0, np.nan, 3.0, 4.0]), horizons=(1,))
    with pytest.raises(ValueError):
        aggregational_kurtosis(np.arange(10.0).reshape(2, 5))


def test_evaluate_additional_facts() -> None:
    passing = {
        "leverage_lag1": -0.1,
        "gain_loss_volatility_ratio": 1.2,
        "dfa_hurst_abs": 0.7,
        "volume_volatility_best_lag": 2,
        "kurtosis_h1": 5.0,
        "kurtosis_h60": 3.5,
    }
    rows = evaluate_additional_facts(passing)
    assert len(rows) == 5
    assert all(row["passes"] for row in rows)
    table = format_additional_table(rows)
    assert "| Additional fact | Statistic | Value | Criterion | Pass |" in table

    failing = dict(passing)
    failing["leverage_lag1"] = 0.1
    rows = evaluate_additional_facts(failing)
    assert rows[0]["passes"] is False


def test_aggregational_table() -> None:
    metrics = {"kurtosis_h1": 5.0, "kurtosis_h5": 4.5, "kurtosis_h20": 4.0, "kurtosis_h60": 3.5}
    table = format_aggregational_table(metrics)
    assert "| Horizon (steps) | Kurtosis |" in table
    assert "| 60 | 3.5 |" in table


def test_write_additional_csv(tmp_path) -> None:
    rows = evaluate_additional_facts(
        {
            "leverage_lag1": -0.1,
            "gain_loss_volatility_ratio": 1.2,
            "dfa_hurst_abs": 0.7,
            "volume_volatility_best_lag": 2,
            "kurtosis_h1": 5.0,
            "kurtosis_h60": 3.5,
        }
    )
    path = write_additional_csv(rows, tmp_path / "additional.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        content = list(csv.DictReader(handle))
    assert len(content) == 5
    assert set(content[0]) == {"fact", "statistic", "value", "criterion", "passes"}
