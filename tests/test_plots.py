from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from market_sim.plots import (  # noqa: E402
    plot_autocorrelation,
    plot_price_series,
    plot_return_histogram,
)


def sample_data() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(123)
    returns = rng.normal(0.0, 0.01, size=2000)
    prices = 100.0 * np.exp(np.cumsum(returns))
    return prices, returns


def test_price_series_figure(tmp_path) -> None:
    prices, _ = sample_data()
    path = plot_price_series(prices, tmp_path / "price.png", fundamental_value=100.0)
    assert path.exists()
    assert path.stat().st_size > 1000


def test_return_histogram_figure(tmp_path) -> None:
    _, returns = sample_data()
    path = plot_return_histogram(returns, tmp_path / "histogram.png", bins=50)
    assert path.exists()
    assert path.stat().st_size > 1000


def test_autocorrelation_figure(tmp_path) -> None:
    _, returns = sample_data()
    path = plot_autocorrelation(returns, tmp_path / "acf.png", max_lag=50)
    assert path.exists()
    assert path.stat().st_size > 1000


def test_histogram_rejects_constant_series(tmp_path) -> None:
    with pytest.raises(ValueError):
        plot_return_histogram(np.ones(100), tmp_path / "bad.png")


def test_autocorrelation_rejects_excessive_lag(tmp_path) -> None:
    _, returns = sample_data()
    with pytest.raises(ValueError):
        plot_autocorrelation(returns, tmp_path / "bad.png", max_lag=returns.size)


def test_price_plot_rejects_non_positive_prices(tmp_path) -> None:
    with pytest.raises(ValueError):
        plot_price_series(np.array([100.0, 0.0, 101.0]), tmp_path / "bad.png")
