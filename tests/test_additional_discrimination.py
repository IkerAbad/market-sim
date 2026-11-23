from __future__ import annotations

import csv

import pytest

from market_sim.additional_discrimination import (
    additional_discrimination_rows,
    format_additional_discrimination_markdown,
    run_model_ensemble,
    run_model_seed,
    samples_from_generator,
    write_additional_discrimination_csv,
)
from market_sim.benchmarks import gaussian_returns
from market_sim.config import MetricsParams, ModelParams, SimulationConfig


def make_config() -> SimulationConfig:
    return SimulationConfig(
        seed=1,
        n_steps=5000,
        burn_in=20,
        model=ModelParams(
            n_agents=20,
            memory_min=2,
            memory_max=10,
            activity_sigma=0.5,
        ),
        metrics=MetricsParams(acf_lags=50),
    )


def make_sample(
    leverage: float,
    asymmetry: float,
    hurst: float,
    aggregation: float,
) -> dict[str, float]:
    return {
        "leverage_lag1": leverage,
        "gain_loss_volatility_ratio": asymmetry,
        "dfa_hurst_abs": hurst,
        "aggregational_ratio": aggregation,
    }


def test_run_model_seed() -> None:
    seed, metrics = run_model_seed(make_config(), 3)
    assert seed == 3
    assert set(metrics) == {
        "leverage_lag1",
        "gain_loss_volatility_ratio",
        "dfa_hurst_abs",
        "aggregational_ratio",
    }


def test_run_model_ensemble_serial_and_parallel() -> None:
    serial = run_model_ensemble(make_config(), [1, 2], jobs=1)
    parallel = run_model_ensemble(make_config(), [1, 2], jobs=2)
    assert len(serial) == 2
    assert len(parallel) == 2
    assert set(serial[0]) == set(parallel[0])


def test_empty_seeds_are_rejected() -> None:
    with pytest.raises(ValueError):
        run_model_ensemble(make_config(), [], jobs=1)


def test_samples_from_generator() -> None:
    samples = samples_from_generator(
        lambda n, seed: gaussian_returns(n, seed=seed),
        n_series=3,
        n=2000,
        base_seed=10,
    )
    assert len(samples) == 3
    assert all("dfa_hurst_abs" in sample for sample in samples)
    with pytest.raises(ValueError):
        samples_from_generator(
            lambda n, seed: gaussian_returns(n, seed=seed),
            n_series=0,
            n=2000,
        )


def test_additional_discrimination_rows() -> None:
    model = [make_sample(-0.05, 1.2, 0.8, 0.6)]
    garch = [make_sample(0.0, 1.0, 0.5, 0.9)]
    gaussian = [make_sample(0.0, 1.0, 0.5, 0.8)]
    rows = additional_discrimination_rows(model, garch, gaussian)
    assert len(rows) == 4
    dfa = next(row for row in rows if row.key == "dfa_hurst_abs")
    assert dfa.auc_garch == 1.0
    assert dfa.auc_gaussian == 1.0
    with pytest.raises(ValueError):
        additional_discrimination_rows([], garch, gaussian)


def test_format_and_csv(tmp_path) -> None:
    model = [make_sample(-0.05, 1.2, 0.8, 0.6)]
    garch = [make_sample(0.0, 1.0, 0.5, 0.9)]
    gaussian = [make_sample(0.0, 1.0, 0.5, 0.8)]
    rows = additional_discrimination_rows(model, garch, gaussian)
    table = format_additional_discrimination_markdown(rows)
    assert "| Additional fact | Model median |" in table
    path = write_additional_discrimination_csv(rows, tmp_path / "additional.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        content = list(csv.DictReader(handle))
    assert len(content) == 4
    assert set(content[0]) == {
        "fact",
        "model_median",
        "garch_median",
        "gaussian_median",
        "auc_garch",
        "auc_gaussian",
    }
