from __future__ import annotations

import numpy as np
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from market_sim.bootstrap import block_indices
from market_sim.config import MetricsParams, ModelParams, SimulationConfig
from market_sim.market import simulate
from market_sim.stylized import autocorrelation, kurtosis, tail_exceedance_ratio

SERIES = st.lists(
    st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    min_size=100,
    max_size=300,
)


@settings(max_examples=20, deadline=None)
@given(SERIES)
def test_autocorrelation_is_bounded(values: list[float]) -> None:
    array = np.asarray(values)
    assume(float(array.std()) > 0.0)
    result = autocorrelation(array, max_lag=10)
    assert result.shape == (11,)
    assert result[0] == 1.0
    assert np.all(np.isfinite(result))
    assert np.all(np.abs(result) <= 1.0 + 1e-12)


@settings(max_examples=20, deadline=None)
@given(SERIES)
def test_kurtosis_is_non_negative(values: list[float]) -> None:
    array = np.asarray(values)
    assume(float(array.std()) > 0.0)
    value = kurtosis(array)
    assert np.isfinite(value)
    assert value >= 0.0


@settings(max_examples=20, deadline=None)
@given(SERIES)
def test_tail_ratio_is_non_negative(values: list[float]) -> None:
    array = np.asarray(values)
    assume(float(array.std()) > 0.0)
    value = tail_exceedance_ratio(array, sigma=2.0)
    assert np.isfinite(value)
    assert value >= 0.0


@settings(max_examples=20, deadline=None)
@given(SERIES, st.floats(min_value=0.1, max_value=10.0))
def test_autocorrelation_is_scale_invariant(values: list[float], scale: float) -> None:
    array = np.asarray(values)
    assume(float(array.std()) > 0.0)
    original = autocorrelation(array, max_lag=5)
    scaled = autocorrelation(array * scale, max_lag=5)
    assert np.allclose(original, scaled, atol=1e-12)


@settings(max_examples=50, deadline=None)
@given(st.integers(min_value=1, max_value=500), st.integers(min_value=1, max_value=50))
def test_block_indices_stay_in_range(n: int, block_length: int) -> None:
    assume(block_length <= n)
    indices = block_indices(n, block_length, np.random.default_rng(n + block_length))
    assert indices.shape == (n,)
    assert indices.min() >= 0
    assert indices.max() < n


@settings(max_examples=5, deadline=None)
@given(
    st.integers(min_value=20, max_value=80),
    st.floats(min_value=0.0, max_value=1.0),
    st.floats(min_value=0.0, max_value=1.0),
)
def test_simulation_is_finite_for_random_parameters(
    n_steps: int, price_impact: float, noise_scale: float
) -> None:
    config = SimulationConfig(
        seed=1,
        n_steps=n_steps,
        burn_in=5,
        model=ModelParams(
            n_agents=15,
            memory_min=2,
            memory_max=10,
            price_impact=price_impact,
            noise_demand_scale=noise_scale,
        ),
        metrics=MetricsParams(acf_lags=50),
    )
    result = simulate(config)
    assert np.all(np.isfinite(result.prices))
    assert np.all(np.isfinite(result.returns))
    assert np.all(np.isfinite(result.volume))
