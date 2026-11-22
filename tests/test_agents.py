from __future__ import annotations

import math

import numpy as np
import pytest

from market_sim.agents import CHARTIST, FUNDAMENTALIST, NOISE, Population
from market_sim.config import ModelParams


def make_params(**overrides: object) -> ModelParams:
    base = {
        "n_agents": 30,
        "fundamentalist_fraction": 0.3,
        "chartist_fraction": 0.4,
        "memory_min": 2,
        "memory_max": 10,
        "activity_sigma": 0.5,
    }
    base.update(overrides)
    return ModelParams(**base)


def test_population_shapes_and_ranges() -> None:
    params = make_params()
    rng = np.random.default_rng(10)
    population = Population.create(params, rng)
    assert population.kind.shape == (30,)
    assert population.memory.shape == (30,)
    assert set(np.unique(population.kind)).issubset({FUNDAMENTALIST, CHARTIST, NOISE})
    assert population.counts() == {"fundamentalist": 9, "chartist": 12, "noise": 9}
    assert np.all(population.memory >= 2)
    assert np.all(population.memory <= 10)
    assert np.all(population.risk_aversion >= 0.5)
    assert np.all(population.risk_aversion <= 2.0)
    assert population.wealth.mean() == pytest.approx(1.0)
    assert np.all(population.activity > 0)


def test_population_is_reproducible() -> None:
    params = make_params()
    first = Population.create(params, np.random.default_rng(99))
    second = Population.create(params, np.random.default_rng(99))
    assert np.array_equal(first.kind, second.kind)
    assert np.array_equal(first.memory, second.memory)
    assert np.array_equal(first.risk_aversion, second.risk_aversion)
    assert np.array_equal(first.wealth, second.wealth)
    assert np.array_equal(first.bias, second.bias)
    assert np.array_equal(first.log_activity, second.log_activity)


def test_demands_are_reproducible() -> None:
    params = make_params()
    prices = np.array([math.log(100.0), math.log(99.0), math.log(98.0)])
    first = Population.create(params, np.random.default_rng(5))
    second = Population.create(params, np.random.default_rng(5))
    first.update_activity(np.random.default_rng(6))
    second.update_activity(np.random.default_rng(6))
    d1 = first.demands(prices, 2, math.log(100.0), np.random.default_rng(7))
    d2 = second.demands(prices, 2, math.log(100.0), np.random.default_rng(7))
    assert np.array_equal(d1, d2)


def test_fundamentalists_buy_below_fundamental_and_sell_above() -> None:
    params = make_params(
        n_agents=20,
        fundamentalist_fraction=1.0,
        chartist_fraction=0.0,
        fundamental_bias_std=0.0,
        activity_sigma=0.0,
    )
    population = Population.create(params, np.random.default_rng(1))
    population.activity = np.ones(20)
    rng = np.random.default_rng(2)
    below = np.array([math.log(90.0), math.log(90.0)])
    above = np.array([math.log(110.0), math.log(110.0)])
    assert np.all(population.demands(below, 1, math.log(100.0), rng) > 0)
    assert np.all(population.demands(above, 1, math.log(100.0), rng) < 0)


def test_chartists_follow_the_trend() -> None:
    params = make_params(
        n_agents=20,
        fundamentalist_fraction=0.0,
        chartist_fraction=1.0,
        memory_min=2,
        memory_max=2,
        activity_sigma=0.0,
        chartist_scale=0.01,
        max_chartist_demand=1.0,
    )
    population = Population.create(params, np.random.default_rng(1))
    population.activity = np.ones(20)
    rising = np.log(np.array([100.0, 101.0, 102.0]))
    falling = np.log(np.array([102.0, 101.0, 100.0]))
    rng = np.random.default_rng(2)
    assert np.all(population.demands(rising, 2, math.log(100.0), rng) > 0)
    assert np.all(population.demands(falling, 2, math.log(100.0), rng) < 0)


def test_zero_noise_scale_gives_zero_noise_demand() -> None:
    params = make_params(
        n_agents=50,
        fundamentalist_fraction=0.0,
        chartist_fraction=0.0,
        activity_sigma=0.0,
        noise_demand_scale=0.0,
    )
    population = Population.create(params, np.random.default_rng(3))
    population.activity = np.ones(50)
    prices = np.array([math.log(100.0)])
    demand = population.demands(prices, 0, math.log(100.0), np.random.default_rng(4))
    assert np.array_equal(demand, np.zeros(50))


def test_risk_aversion_scales_demand() -> None:
    params = make_params(
        n_agents=20,
        fundamentalist_fraction=1.0,
        chartist_fraction=0.0,
        fundamental_bias_std=0.0,
        activity_sigma=0.0,
    )
    population = Population.create(params, np.random.default_rng(1))
    population.activity = np.ones(20)
    prices = np.array([math.log(90.0), math.log(90.0)])
    population.risk_aversion = np.ones(20)
    low_risk = population.demands(prices, 1, math.log(100.0), np.random.default_rng(2))
    population.risk_aversion = np.full(20, 2.0)
    high_risk = population.demands(prices, 1, math.log(100.0), np.random.default_rng(2))
    assert np.allclose(low_risk, 2.0 * high_risk)


def test_activity_has_unit_mean() -> None:
    params = make_params(
        n_agents=5000,
        memory_min=5,
        memory_max=100,
        activity_sigma=0.5,
    )
    population = Population.create(params, np.random.default_rng(11))
    rng = np.random.default_rng(12)
    for _ in range(200):
        population.update_activity(rng)
    assert abs(float(population.activity.mean()) - 1.0) < 0.05
