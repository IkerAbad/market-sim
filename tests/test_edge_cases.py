from __future__ import annotations

import importlib

import numpy as np
import pytest

from market_sim.ablations import (
    ABLATIONS,
    ablation_report,
    run_ablation_grid,
    summarize_ablations,
)
from market_sim.ablations import (
    _float_metric as ablation_float_metric,
)
from market_sim.benchmarks import (
    benchmark_metrics,
    garch11_returns,
    gaussian_returns,
    student_t_returns,
)
from market_sim.config import (
    MetricsParams,
    ModelParams,
    SimulationConfig,
    _coerce,
)
from market_sim.ensemble import parse_seeds
from market_sim.extra_facts import dfa_hurst, gain_loss_asymmetry
from market_sim.phase import (
    _float_metric as phase_float_metric,
)
from market_sim.phase import (
    run_phase_grid,
)
from market_sim.price_volume import price_diagnostics, volume_diagnostics
from market_sim.real_data import load_returns_csv
from market_sim.sample_size import (
    SampleSizePoint,
    run_sample_size_grid,
    summarize_sample_size,
)
from market_sim.sample_size import (
    _float_metric as sample_float_metric,
)
from market_sim.stylized import correlation
from market_sim.thresholds import evaluate_thresholds


def make_config() -> SimulationConfig:
    return SimulationConfig(
        seed=1,
        n_steps=200,
        burn_in=20,
        model=ModelParams(n_agents=20, memory_min=2, memory_max=10),
        metrics=MetricsParams(acf_lags=50),
    )


class FakeFuture:
    def __init__(self, value: object) -> None:
        self.value = value

    def result(self) -> object:
        return self.value


class FakeExecutor:
    def __init__(self, max_workers: int) -> None:
        self.max_workers = max_workers

    def __enter__(self) -> FakeExecutor:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def submit(self, function, *args):
        return FakeFuture(function(*args))


def test_config_coerce() -> None:
    assert _coerce("true", True) is True
    assert _coerce("false", True) is False
    assert _coerce("yes", True) is True
    assert _coerce("no", True) is False
    assert _coerce("1", True) is True
    assert _coerce("0", True) is False
    assert _coerce("3", 2) == 3
    assert _coerce("2.5", 1.0) == 2.5
    assert _coerce(5, 1.0) == 5
    with pytest.raises(ValueError):
        _coerce("maybe", True)


def test_negative_burn_in_raises() -> None:
    with pytest.raises(ValueError):
        SimulationConfig(
            seed=1,
            n_steps=100,
            burn_in=-1,
            model=ModelParams(),
            metrics=MetricsParams(),
        )


def test_benchmark_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        gaussian_returns(0)
    with pytest.raises(ValueError):
        student_t_returns(0)
    with pytest.raises(ValueError):
        student_t_returns(100, df=2.0)
    with pytest.raises(ValueError):
        garch11_returns(0)
    with pytest.raises(ValueError):
        garch11_returns(100, omega=0.0)
    with pytest.raises(ValueError):
        garch11_returns(100, alpha=0.5, beta=0.6)


def test_benchmark_metrics_invalid_inputs() -> None:
    params = MetricsParams(acf_lags=50)
    with pytest.raises(ValueError):
        benchmark_metrics(np.ones(10), params)
    values = np.ones(100)
    values[0] = np.nan
    with pytest.raises(ValueError):
        benchmark_metrics(values, params)


def test_extra_facts_edge_cases() -> None:
    with pytest.raises(ValueError):
        gain_loss_asymmetry(np.array([-1.0, -1.0, 1.0, 1.0]))
    with pytest.raises(ValueError):
        dfa_hurst(np.arange(100.0), scales=[8, 16, 64])


def test_threshold_edge_cases() -> None:
    with pytest.raises(ValueError):
        evaluate_thresholds([])
    rows = [
        {
            "kurtosis": 5.0,
            "acf_return_lag1": 0.0,
            "acf_abs_return_lag1": 0.1,
            "acf_abs_return_lag50": 0.1,
            "corr_volume_abs_return": 0.5,
            "tail_exceedance_ratio": 10.0,
        }
    ]
    with pytest.raises(ValueError):
        evaluate_thresholds(rows, (("Bad", "kurtosis", "==", (3.0,)),))


def test_real_data_skips_blank_values(tmp_path) -> None:
    path = tmp_path / "blank.csv"
    path.write_text("return\n0.01\n\n0.02\n", encoding="utf-8")
    values = load_returns_csv(path)
    assert values.size == 2


def test_private_float_helpers_reject_missing_values() -> None:
    with pytest.raises(ValueError):
        phase_float_metric({}, "kurtosis")
    with pytest.raises(ValueError):
        ablation_float_metric({}, "kurtosis")
    with pytest.raises(ValueError):
        sample_float_metric({}, "kurtosis")


def test_phase_single_cell_with_jobs() -> None:
    points = run_phase_grid(make_config(), [1.0], [0.1], [1], jobs=2)
    assert len(points) == 1


def test_ablation_process_pool(monkeypatch) -> None:
    monkeypatch.setattr("market_sim.ablations.ProcessPoolExecutor", FakeExecutor)
    results = run_ablation_grid(make_config(), ABLATIONS[:2], [1, 2], jobs=2)
    assert len(results) == 4


def test_full_ablation_report() -> None:
    results = run_ablation_grid(make_config(), ABLATIONS, [1], jobs=1)
    summary = summarize_ablations(results, ABLATIONS)
    report = ablation_report(summary, "python scripts/run_ablations.py")
    assert "noise_only" in report
    assert "not the source of the statistical facts" in report


def test_sample_size_process_pool(monkeypatch) -> None:
    monkeypatch.setattr("market_sim.sample_size.ProcessPoolExecutor", FakeExecutor)
    results = run_sample_size_grid(make_config(), [2000, 4000], [1, 2], jobs=2)
    assert len(results) == 4


def test_sample_size_all_pass_count() -> None:
    metrics = {
        "kurtosis": 5.0,
        "acf_return_lag1": 0.0,
        "acf_abs_return_lag1": 0.2,
        "acf_abs_return_lag50": 0.1,
        "corr_volume_abs_return": 0.5,
        "tail_exceedance_ratio": 10.0,
    }
    point = SampleSizePoint(
        size=2000,
        seed=1,
        metrics=metrics,
        passes=(True, True, True, True, True, True),
        pass_count=6,
        all_pass=True,
    )
    summary = summarize_sample_size([point])
    assert summary.all_pass_count[0] == 1


def test_stylized_correlation_non_finite() -> None:
    with pytest.raises(ValueError):
        correlation(np.array([1.0, np.nan, 2.0]), np.array([1.0, 2.0, 3.0]))


def test_price_volume_non_finite() -> None:
    with pytest.raises(ValueError):
        price_diagnostics(np.array([1.0, np.nan, 2.0]), 100.0)
    with pytest.raises(ValueError):
        volume_diagnostics(
            np.array([1.0, np.nan, 2.0]),
            np.array([0.1, 0.2, 0.3]),
        )


def test_parse_seeds_negative_is_clear() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        parse_seeds("-1")


def test_main_module_import() -> None:
    module = importlib.import_module("market_sim.__main__")
    assert module is not None
