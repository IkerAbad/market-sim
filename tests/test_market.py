from __future__ import annotations

import numpy as np
import pytest

from market_sim.agents import Population
from market_sim.config import MetricsParams, ModelParams, SimulationConfig
from market_sim.market import load_series_csv, save_series_csv, simulate


def make_config(**model_overrides: object) -> SimulationConfig:
    model_values = {
        "n_agents": 40,
        "memory_min": 2,
        "memory_max": 10,
        "activity_sigma": 0.5,
    }
    model_values.update(model_overrides)
    return SimulationConfig(
        seed=1234,
        n_steps=500,
        burn_in=50,
        model=ModelParams(**model_values),
        metrics=MetricsParams(acf_lags=50),
    )


def test_simulation_shapes_and_finiteness() -> None:
    result = simulate(make_config())
    assert result.prices.shape == (501,)
    assert result.returns.shape == (500,)
    assert result.volume.shape == (500,)
    assert np.all(np.isfinite(result.prices))
    assert np.all(np.isfinite(result.returns))
    assert np.all(np.isfinite(result.volume))
    assert np.all(result.volume >= 0)
    assert np.all(np.exp(result.prices) > 0)


def test_same_seed_same_series() -> None:
    first = simulate(make_config())
    second = simulate(make_config())
    assert np.array_equal(first.prices, second.prices)
    assert np.array_equal(first.returns, second.returns)
    assert np.array_equal(first.volume, second.volume)


def test_different_seed_different_series() -> None:
    first = simulate(make_config())
    second_config = make_config()
    second_config = SimulationConfig(
        seed=1235,
        n_steps=second_config.n_steps,
        burn_in=second_config.burn_in,
        model=second_config.model,
        metrics=second_config.metrics,
    )
    second = simulate(second_config)
    assert not np.array_equal(first.returns, second.returns)


def test_analysis_window_uses_burn_in() -> None:
    result = simulate(make_config())
    returns, volume = result.analysis_window()
    assert returns.size == 450
    assert volume.size == 450
    assert np.array_equal(returns, result.returns[50:])
    assert result.price_window().size == 451


def test_csv_roundtrip(tmp_path) -> None:
    result = simulate(make_config())
    path = save_series_csv(result, tmp_path / "series.csv")
    data = load_series_csv(path)
    assert set(data) == {"step", "price", "log_price", "return", "volume"}
    assert data["step"].size == 450
    assert data["step"][0] == 51
    assert data["step"][-1] == 500
    assert np.allclose(data["price"], np.exp(data["log_price"]))
    assert np.allclose(data["return"], result.returns[50:], atol=1e-9, rtol=1e-9)
    assert np.allclose(data["volume"], result.volume[50:], atol=1e-9, rtol=1e-9)


def test_extreme_parameters_do_not_explode() -> None:
    config = SimulationConfig(
        seed=77,
        n_steps=1500,
        burn_in=10,
        model=ModelParams(
            n_agents=20,
            memory_min=2,
            memory_max=100,
            activity_sigma=3.0,
            price_impact=25.0,
            kappa_fundamentalist=100.0,
            kappa_chartist=100.0,
            fundamental_scale=0.01,
            chartist_scale=0.0001,
            max_fundamentalist_demand=50.0,
            max_chartist_demand=50.0,
            noise_demand_scale=50.0,
        ),
        metrics=MetricsParams(acf_lags=50),
    )
    result = simulate(config)
    assert np.all(np.isfinite(result.prices))
    assert np.all(np.isfinite(result.returns))
    assert np.all(np.isfinite(result.volume))


def test_zero_demand_is_a_fixed_point() -> None:
    config = SimulationConfig(
        seed=1,
        n_steps=100,
        burn_in=10,
        model=ModelParams(
            n_agents=20,
            fundamentalist_fraction=1.0,
            chartist_fraction=0.0,
            fundamental_bias_std=0.0,
            activity_sigma=0.0,
            price_impact=0.1,
        ),
        metrics=MetricsParams(acf_lags=50),
    )
    result = simulate(config)
    assert np.array_equal(result.returns, np.zeros(100))
    assert np.allclose(result.prices, np.log(100.0))
    assert np.array_equal(result.volume, np.zeros(100))


def test_zero_price_impact_leaves_price_unchanged() -> None:
    config = SimulationConfig(
        seed=2,
        n_steps=100,
        burn_in=10,
        model=ModelParams(n_agents=20, price_impact=0.0),
        metrics=MetricsParams(acf_lags=50),
    )
    result = simulate(config)
    assert np.array_equal(result.returns, np.zeros(100))
    assert np.allclose(result.prices, np.log(100.0))
    assert np.any(result.volume > 0)


def test_save_creates_parent_directories(tmp_path) -> None:
    result = simulate(make_config())
    path = save_series_csv(result, tmp_path / "nested" / "series.csv")
    assert path.exists()


def test_load_rejects_missing_header(tmp_path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError):
        load_series_csv(path)


def test_non_finite_guard(monkeypatch) -> None:
    def bad_demands(
        self: Population,
        prices: np.ndarray,
        t: int,
        fundamental_log: float,
        rng: np.random.Generator,
    ) -> np.ndarray:
        return np.full(self.kind.size, np.nan)

    monkeypatch.setattr(Population, "demands", bad_demands)
    with pytest.raises(FloatingPointError):
        simulate(make_config())
