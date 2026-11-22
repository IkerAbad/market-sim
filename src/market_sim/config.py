"""Configuration objects and JSON loading.

The configuration is deliberately explicit: every number that enters a run is
stored in the JSON file, including the seed.  The dataclasses below validate
the values before any simulation starts.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class ModelParams:
    """Parameters of the agent population and the price-impact rule."""

    n_agents: int = 200
    fundamentalist_fraction: float = 0.30
    chartist_fraction: float = 0.40
    memory_min: int = 5
    memory_max: int = 1000
    risk_aversion_min: float = 0.5
    risk_aversion_max: float = 2.0
    wealth_min: float = 0.5
    wealth_max: float = 1.5
    fundamental_bias_std: float = 0.03
    activity_sigma: float = 1.0
    price_impact: float = 0.05
    kappa_fundamentalist: float = 1.0
    kappa_chartist: float = 1.0
    fundamental_scale: float = 1.0
    chartist_scale: float = 0.002
    max_fundamentalist_demand: float = 1.0
    max_chartist_demand: float = 0.1
    noise_demand_scale: float = 1.0
    fundamental_value: float = 100.0

    def __post_init__(self) -> None:
        if self.n_agents < 1:
            raise ValueError("n_agents must be at least 1")
        if self.fundamentalist_fraction < 0 or self.chartist_fraction < 0:
            raise ValueError("agent fractions cannot be negative")
        if self.fundamentalist_fraction + self.chartist_fraction > 1.0 + 1e-12:
            raise ValueError("fundamentalist_fraction + chartist_fraction cannot exceed 1")
        if self.memory_min < 1 or self.memory_max < self.memory_min:
            raise ValueError("memory must satisfy 1 <= memory_min <= memory_max")
        if self.risk_aversion_min <= 0 or self.risk_aversion_max < self.risk_aversion_min:
            raise ValueError("risk aversion must satisfy 0 < min <= max")
        if self.wealth_min <= 0 or self.wealth_max < self.wealth_min:
            raise ValueError("wealth must satisfy 0 < min <= max")
        if self.fundamental_bias_std < 0:
            raise ValueError("fundamental_bias_std cannot be negative")
        if self.activity_sigma < 0:
            raise ValueError("activity_sigma cannot be negative")
        if self.price_impact < 0:
            raise ValueError("price_impact cannot be negative")
        if self.kappa_fundamentalist < 0 or self.kappa_chartist < 0:
            raise ValueError("kappa values cannot be negative")
        if self.fundamental_scale <= 0 or self.chartist_scale <= 0:
            raise ValueError("demand scales must be positive")
        if (
            self.max_fundamentalist_demand < 0
            or self.max_chartist_demand < 0
            or self.noise_demand_scale < 0
        ):
            raise ValueError("demand magnitudes cannot be negative")
        if self.fundamental_value <= 0:
            raise ValueError("fundamental_value must be positive")


@dataclass(frozen=True)
class MetricsParams:
    """Thresholds used to classify each stylized fact as reproduced or not."""

    acf_lags: int = 200
    tail_sigma: float = 4.0
    kurtosis_threshold: float = 3.0
    return_acf_threshold: float = 0.05
    abs_acf_lag1_threshold: float = 0.05
    abs_acf_lag50_threshold: float = 0.02
    volume_corr_threshold: float = 0.2
    tail_ratio_threshold: float = 1.0

    def __post_init__(self) -> None:
        if self.acf_lags < 50:
            raise ValueError("acf_lags must be at least 50")
        if self.tail_sigma <= 0:
            raise ValueError("tail_sigma must be positive")
        if self.kurtosis_threshold < 0:
            raise ValueError("kurtosis_threshold cannot be negative")
        if self.return_acf_threshold < 0:
            raise ValueError("return_acf_threshold cannot be negative")
        if self.abs_acf_lag1_threshold < 0:
            raise ValueError("abs_acf_lag1_threshold cannot be negative")
        if self.abs_acf_lag50_threshold < 0:
            raise ValueError("abs_acf_lag50_threshold cannot be negative")
        if self.volume_corr_threshold < 0:
            raise ValueError("volume_corr_threshold cannot be negative")
        if self.tail_ratio_threshold < 0:
            raise ValueError("tail_ratio_threshold cannot be negative")


@dataclass(frozen=True)
class SimulationConfig:
    """Complete configuration of one reproducible run."""

    seed: int
    n_steps: int
    burn_in: int
    model: ModelParams
    metrics: MetricsParams

    def __post_init__(self) -> None:
        if self.seed < 0:
            raise ValueError("seed must be non-negative")
        if self.n_steps < 1:
            raise ValueError("n_steps must be at least 1")
        if self.burn_in < 0:
            raise ValueError("burn_in cannot be negative")
        if self.burn_in >= self.n_steps:
            raise ValueError("burn_in must be smaller than n_steps")


def config_from_dict(data: Mapping[str, Any]) -> SimulationConfig:
    """Build a validated configuration from a mapping."""
    try:
        model = ModelParams(**data["model"])
        metrics = MetricsParams(**data["metrics"])
        return SimulationConfig(
            seed=int(data["seed"]),
            n_steps=int(data["n_steps"]),
            burn_in=int(data["burn_in"]),
            model=model,
            metrics=metrics,
        )
    except KeyError as exc:
        raise ValueError(f"missing configuration key: {exc.args[0]}") from exc
    except TypeError as exc:
        raise ValueError(f"unknown or missing configuration field: {exc}") from exc


def load_config(path: str | Path) -> SimulationConfig:
    """Load a JSON configuration file."""
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("the configuration root must be a JSON object")
    return config_from_dict(data)


def config_to_dict(config: SimulationConfig) -> dict[str, Any]:
    """Return a JSON-serialisable representation of a configuration."""
    return asdict(config)


def _coerce(value: Any, current: Any) -> Any:
    if isinstance(value, str):
        if isinstance(current, bool):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
            raise ValueError(f"cannot parse boolean value {value!r}")
        if isinstance(current, int):
            return int(value)
        if isinstance(current, float):
            return float(value)
    return value


def apply_overrides(
    config: SimulationConfig, overrides: Mapping[str, Any]
) -> SimulationConfig:
    """Return a new configuration with dotted-key overrides applied.

    Keys use the JSON layout, for example ``model.price_impact`` or ``seed``.
    """
    data = config_to_dict(config)
    for dotted_key, raw_value in overrides.items():
        parts = dotted_key.split(".")
        target: Any = data
        for part in parts[:-1]:
            if not isinstance(target, dict) or part not in target:
                raise KeyError(f"unknown configuration key: {dotted_key}")
            target = target[part]
        leaf = parts[-1]
        if not isinstance(target, dict) or leaf not in target:
            raise KeyError(f"unknown configuration key: {dotted_key}")
        target[leaf] = _coerce(raw_value, target[leaf])
    return config_from_dict(data)
