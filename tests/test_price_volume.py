from __future__ import annotations

import csv

import numpy as np
import pytest

from market_sim.price_volume import (
    format_diagnostics_markdown,
    price_diagnostics,
    run_diagnostics,
    volume_diagnostics,
    write_diagnostics_csv,
)


def sample_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(1)
    returns = rng.normal(0.0, 0.01, size=1000)
    volume = np.abs(returns) * 100.0 + rng.random(1000)
    log_prices = np.log(100.0) + 0.01 * 0.9 ** np.arange(1000)
    return log_prices, returns, volume


def test_price_diagnostics_ar1() -> None:
    log_prices, _, _ = sample_data()
    metrics = price_diagnostics(log_prices, 100.0)
    assert metrics["gap_ar1"] == pytest.approx(0.9, abs=1e-9)
    assert metrics["gap_half_life"] == pytest.approx(-np.log(2.0) / np.log(0.9))
    assert metrics["price_min"] > 99.0
    assert metrics["price_max"] < 101.01


def test_volume_diagnostics() -> None:
    _, returns, volume = sample_data()
    metrics = volume_diagnostics(volume, returns)
    assert metrics["volume_kurtosis"] > 0
    assert np.isfinite(metrics["volume_acf1"])
    assert -1.0 <= metrics["corr_volume_abs_return"] <= 1.0


def test_run_diagnostics_and_outputs(tmp_path) -> None:
    log_prices, returns, volume = sample_data()
    metrics = run_diagnostics(log_prices, returns, volume, 100.0)
    assert len(metrics) == 15
    table = format_diagnostics_markdown(metrics)
    assert "| Statistic | Value |" in table
    assert "Log gap half-life" in table
    path = write_diagnostics_csv(metrics, tmp_path / "diagnostics.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 15
    assert set(rows[0]) == {"statistic", "value"}


def test_diagnostics_reject_bad_inputs() -> None:
    log_prices, returns, volume = sample_data()
    with pytest.raises(ValueError):
        price_diagnostics(np.ones(100), 100.0)
    with pytest.raises(ValueError):
        price_diagnostics(log_prices, 0.0)
    with pytest.raises(ValueError):
        volume_diagnostics(volume[:-1], returns)
    with pytest.raises(ValueError):
        volume_diagnostics(np.ones(100), returns[:100])
    with pytest.raises(ValueError):
        price_diagnostics(np.array([1.0, 2.0]), 100.0)
    with pytest.raises(ValueError):
        volume_diagnostics(np.array([1.0, 2.0]), np.array([0.1, 0.2]))
