from __future__ import annotations

import csv

import numpy as np
import pytest

from market_sim.bootstrap import (
    block_indices,
    bootstrap_metrics,
    format_bootstrap_markdown,
    write_bootstrap_csv,
)
from market_sim.config import MetricsParams


def sample_series(n: int = 600) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(7)
    returns = rng.normal(0.0, 0.01, size=n)
    returns[::37] *= 4.0
    volume = np.abs(returns) + 0.2
    return returns, volume


def test_block_indices_shape_and_bounds() -> None:
    rng = np.random.default_rng(1)
    indices = block_indices(100, 10, rng)
    assert indices.shape == (100,)
    assert indices.min() >= 0
    assert indices.max() < 100


def test_block_indices_are_contiguous() -> None:
    rng = np.random.default_rng(2)
    indices = block_indices(30, 5, rng)
    for start in (0, 5, 10, 15, 20, 25):
        block = indices[start : start + 5]
        assert np.array_equal(np.diff(block), np.ones(4, dtype=int))


def test_block_indices_reject_bad_lengths() -> None:
    rng = np.random.default_rng(3)
    with pytest.raises(ValueError):
        block_indices(10, 0, rng)
    with pytest.raises(ValueError):
        block_indices(10, 11, rng)
    with pytest.raises(ValueError):
        block_indices(0, 1, rng)


def test_bootstrap_metrics() -> None:
    returns, volume = sample_series()
    result = bootstrap_metrics(
        returns,
        volume,
        MetricsParams(acf_lags=50),
        n_resamples=20,
        block_length=50,
        seed=11,
    )
    assert len(result.summaries) == 6
    assert result.n_resamples == 20
    assert result.block_length == 50
    for item in result.summaries:
        assert np.isfinite(item.point)
        assert np.isfinite(item.mean)
        assert np.isfinite(item.lower)
        assert np.isfinite(item.upper)
        assert item.lower <= item.upper
    table = format_bootstrap_markdown(result)
    assert "| Statistic | Point estimate | Bootstrap mean | 95% interval |" in table
    assert "Kurtosis" in table


def test_bootstrap_is_reproducible() -> None:
    returns, volume = sample_series()
    params = MetricsParams(acf_lags=50)
    first = bootstrap_metrics(returns, volume, params, 10, 50, seed=5)
    second = bootstrap_metrics(returns, volume, params, 10, 50, seed=5)
    assert first == second


def test_bootstrap_rejects_invalid_inputs() -> None:
    returns, volume = sample_series()
    params = MetricsParams(acf_lags=50)
    with pytest.raises(ValueError):
        bootstrap_metrics(returns, volume, params, n_resamples=0)
    with pytest.raises(ValueError):
        bootstrap_metrics(returns, volume[:-1], params)
    with pytest.raises(ValueError):
        bootstrap_metrics(returns, volume, params, confidence=1.0)
    with pytest.raises(ValueError):
        bootstrap_metrics(returns, volume, params, block_length=0)


def test_bootstrap_rejects_short_or_non_finite_series() -> None:
    params = MetricsParams(acf_lags=50)
    with pytest.raises(ValueError):
        bootstrap_metrics(np.array([1.0]), np.array([1.0]), params)
    returns, volume = sample_series()
    bad_returns = returns.copy()
    bad_returns[0] = np.nan
    with pytest.raises(ValueError):
        bootstrap_metrics(bad_returns, volume, params)
    bad_volume = volume.copy()
    bad_volume[0] = np.inf
    with pytest.raises(ValueError):
        bootstrap_metrics(returns, bad_volume, params)


def test_write_bootstrap_csv(tmp_path) -> None:
    returns, volume = sample_series()
    result = bootstrap_metrics(
        returns,
        volume,
        MetricsParams(acf_lags=50),
        n_resamples=5,
        block_length=50,
        seed=1,
    )
    path = write_bootstrap_csv(result, tmp_path / "inference.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 6
    assert set(rows[0]) == {"statistic", "point", "mean", "lower", "upper"}
