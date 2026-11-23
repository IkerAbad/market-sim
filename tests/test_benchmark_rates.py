from __future__ import annotations

import csv

import pytest

from market_sim.benchmark_rates import (
    FACT_KEYS,
    format_rates_markdown,
    metrics_from_generator,
    rate_generator,
    rate_metrics,
    rates_from_metrics_csv,
    write_rates_csv,
)
from market_sim.benchmarks import gaussian_returns
from market_sim.config import MetricsParams

PARAMS = MetricsParams(acf_lags=50)

PASSING = {
    "kurtosis": 5.0,
    "acf_return_lag1": 0.0,
    "acf_abs_return_lag1": 0.2,
    "acf_abs_return_lag50": 0.1,
    "tail_exceedance_ratio": 10.0,
}

FAILING = {
    "kurtosis": 2.0,
    "acf_return_lag1": 0.2,
    "acf_abs_return_lag1": 0.0,
    "acf_abs_return_lag50": 0.0,
    "tail_exceedance_ratio": 0.5,
}


def test_rate_metrics_counts_each_fact() -> None:
    rate = rate_metrics("test", "fixture", [PASSING, FAILING], PARAMS)
    assert rate.n_series == 2
    assert rate.all_pass == 1
    assert [fact.passes for fact in rate.facts] == [1, 1, 1, 1, 1]
    assert all(fact.total == 2 for fact in rate.facts)
    assert rate.facts[0].rate == 0.5


def test_empty_metrics_are_rejected() -> None:
    with pytest.raises(ValueError):
        rate_metrics("test", "fixture", [], PARAMS)


def test_zero_series_are_rejected() -> None:
    with pytest.raises(ValueError):
        metrics_from_generator(
            lambda n, seed: gaussian_returns(n, seed=seed),
            PARAMS,
            n_series=0,
            n=2000,
        )


def test_gaussian_rates() -> None:
    rate = rate_generator(
        "Gaussian",
        "fixture",
        lambda n, seed: gaussian_returns(n, seed=seed),
        PARAMS,
        n_series=5,
        n=2000,
    )
    assert rate.n_series == 5
    assert rate.all_pass == 0
    assert all(fact.total == 5 for fact in rate.facts)
    assert rate.facts[0].passes < 5


def test_rates_from_metrics_csv(tmp_path) -> None:
    path = tmp_path / "metrics.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([key for key, _ in FACT_KEYS])
        for metrics in (PASSING, FAILING):
            writer.writerow([metrics[key] for key, _ in FACT_KEYS])
    rate = rates_from_metrics_csv(path, "model", "fixture", PARAMS)
    assert rate.n_series == 2
    assert rate.all_pass == 1


def test_empty_metrics_csv_is_rejected(tmp_path) -> None:
    path = tmp_path / "metrics.csv"
    path.write_text("kurtosis\n", encoding="utf-8")
    with pytest.raises(ValueError):
        rates_from_metrics_csv(path, "model", "fixture", PARAMS)


def test_format_and_csv(tmp_path) -> None:
    rates = [
        rate_metrics("first", "fixture", [PASSING, FAILING], PARAMS),
        rate_metrics("second", "fixture", [PASSING], PARAMS),
    ]
    table = format_rates_markdown(rates)
    assert "| Series | Kurtosis |" in table
    assert "| first | 1/2 |" in table
    assert "95% CI" in table
    assert rate_metrics("x", "y", [PASSING], PARAMS).all_pass_interval[1] == pytest.approx(1.0)
    path = write_rates_csv(rates, tmp_path / "rates.csv")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("series,n_series,kurtosis")
