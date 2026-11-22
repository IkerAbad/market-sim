from __future__ import annotations

from pathlib import Path

import pytest

from market_sim.config import (
    MetricsParams,
    ModelParams,
    SimulationConfig,
    apply_overrides,
    config_from_dict,
    config_to_dict,
    load_config,
)

ROOT = Path(__file__).resolve().parents[1]


def test_load_baseline_config() -> None:
    config = load_config(ROOT / "configs" / "baseline.json")
    assert config.seed == 20261122
    assert config.n_steps == 101000
    assert config.burn_in == 1000
    assert config.model.n_agents == 200
    assert config.metrics.acf_lags == 200


def test_config_roundtrip() -> None:
    config = load_config(ROOT / "configs" / "baseline.json")
    rebuilt = config_from_dict(config_to_dict(config))
    assert rebuilt == config


def test_apply_overrides() -> None:
    config = load_config(ROOT / "configs" / "baseline.json")
    changed = apply_overrides(
        config,
        {"seed": "7", "model.price_impact": "0.2", "metrics.acf_lags": "100"},
    )
    assert changed.seed == 7
    assert changed.model.price_impact == 0.2
    assert changed.metrics.acf_lags == 100
    assert changed.model.n_agents == config.model.n_agents


def test_unknown_override_raises() -> None:
    config = load_config(ROOT / "configs" / "baseline.json")
    with pytest.raises(KeyError):
        apply_overrides(config, {"model.not_a_parameter": "1"})


def test_invalid_fractions_raise() -> None:
    with pytest.raises(ValueError):
        ModelParams(fundamentalist_fraction=0.7, chartist_fraction=0.4)


def test_invalid_burn_in_raises() -> None:
    with pytest.raises(ValueError):
        SimulationConfig(
            seed=1,
            n_steps=100,
            burn_in=100,
            model=ModelParams(),
            metrics=MetricsParams(),
        )


def test_negative_seed_raises() -> None:
    with pytest.raises(ValueError):
        SimulationConfig(
            seed=-1,
            n_steps=100,
            burn_in=10,
            model=ModelParams(),
            metrics=MetricsParams(),
        )
