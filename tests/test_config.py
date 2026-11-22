from __future__ import annotations

import json
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


def test_bad_override_value_raises() -> None:
    config = load_config(ROOT / "configs" / "baseline.json")
    with pytest.raises(ValueError):
        apply_overrides(config, {"seed": "not-an-integer"})


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


@pytest.mark.parametrize(
    "overrides",
    [
        {"n_agents": 0},
        {"fundamentalist_fraction": -0.1},
        {"chartist_fraction": 1.1},
        {"memory_min": 0},
        {"memory_min": 5, "memory_max": 4},
        {"risk_aversion_min": 0.0},
        {"risk_aversion_min": 2.0, "risk_aversion_max": 1.0},
        {"wealth_min": 0.0},
        {"wealth_min": 2.0, "wealth_max": 1.0},
        {"fundamental_bias_std": -1.0},
        {"activity_sigma": -1.0},
        {"price_impact": -1.0},
        {"kappa_fundamentalist": -1.0},
        {"kappa_chartist": -1.0},
        {"fundamental_scale": 0.0},
        {"chartist_scale": 0.0},
        {"max_fundamentalist_demand": -1.0},
        {"max_chartist_demand": -1.0},
        {"noise_demand_scale": -1.0},
        {"fundamental_value": 0.0},
    ],
)
def test_invalid_model_values_raise(overrides: dict[str, float | int]) -> None:
    with pytest.raises(ValueError):
        ModelParams(**overrides)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "overrides",
    [
        {"acf_lags": 49},
        {"tail_sigma": 0.0},
        {"kurtosis_threshold": -1.0},
        {"return_acf_threshold": -1.0},
        {"abs_acf_lag1_threshold": -1.0},
        {"abs_acf_lag50_threshold": -1.0},
        {"volume_corr_threshold": -1.0},
        {"tail_ratio_threshold": -1.0},
    ],
)
def test_invalid_metric_values_raise(overrides: dict[str, float | int]) -> None:
    with pytest.raises(ValueError):
        MetricsParams(**overrides)  # type: ignore[arg-type]


def test_invalid_step_count_raises() -> None:
    with pytest.raises(ValueError):
        SimulationConfig(
            seed=1,
            n_steps=0,
            burn_in=0,
            model=ModelParams(),
            metrics=MetricsParams(),
        )


def test_load_config_rejects_non_object(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(TypeError):
        load_config(path)


def test_load_config_rejects_missing_section(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"seed": 1}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)


def test_load_config_rejects_unknown_field(tmp_path) -> None:
    data = config_to_dict(load_config(ROOT / "configs" / "baseline.json"))
    data["model"]["unknown_parameter"] = 1
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)
