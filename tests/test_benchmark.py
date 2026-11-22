from __future__ import annotations

import pytest

from market_sim.benchmark import BenchmarkResult, time_simulation
from market_sim.config import MetricsParams, ModelParams, SimulationConfig


def make_config() -> SimulationConfig:
    return SimulationConfig(
        seed=1,
        n_steps=100,
        burn_in=10,
        model=ModelParams(n_agents=20, memory_min=2, memory_max=10),
        metrics=MetricsParams(acf_lags=50),
    )


def test_time_simulation() -> None:
    result = time_simulation(make_config(), steps=500, repeat=2)
    assert result.steps == 500
    assert result.n_agents == 20
    assert result.runs == 2
    assert result.best_seconds > 0
    assert result.mean_seconds >= result.best_seconds
    assert result.steps_per_second > 0
    assert result.agent_steps_per_second > 0


def test_benchmark_result_properties() -> None:
    result = BenchmarkResult(
        steps=100,
        n_agents=10,
        best_seconds=0.5,
        mean_seconds=1.0,
        runs=1,
    )
    assert result.steps_per_second == 100.0
    assert result.agent_steps_per_second == 1000.0


def test_time_simulation_rejects_bad_values() -> None:
    with pytest.raises(ValueError):
        time_simulation(make_config(), steps=0)
    with pytest.raises(ValueError):
        time_simulation(make_config(), steps=10, repeat=0)
