from __future__ import annotations

import csv

import pytest

from market_sim.config import MetricsParams
from market_sim.null_distribution import (
    format_null_markdown,
    null_statistics,
    write_null_csv,
)

PARAMS = MetricsParams(acf_lags=50)

MODEL = {
    "kurtosis": 10.0,
    "acf_return_lag1": 0.0,
    "acf_abs_return_lag1": 0.2,
    "acf_abs_return_lag50": 0.1,
    "tail_exceedance_ratio": 10.0,
}


def test_null_statistics() -> None:
    rows = null_statistics(PARAMS, MODEL, n_series=20, n=2000)
    assert len(rows) == 5
    for row in rows:
        assert row.q05 <= row.median <= row.q95
        assert 0.0 <= row.model_percentile <= 1.0
    kurtosis = next(row for row in rows if row.key == "kurtosis")
    assert kurtosis.model_percentile == 1.0
    assert kurtosis.q05 < 3.0 < kurtosis.q95


def test_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        null_statistics(PARAMS, MODEL, n_series=0, n=2000)
    with pytest.raises(ValueError):
        null_statistics(PARAMS, MODEL, n_series=5, n=10)


def test_format_and_csv(tmp_path) -> None:
    rows = null_statistics(PARAMS, MODEL, n_series=10, n=2000)
    table = format_null_markdown(rows)
    assert "| Statistic | Gaussian 5% | Median | 95% | Model | Model percentile |" in table
    path = write_null_csv(rows, tmp_path / "null.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        content = list(csv.DictReader(handle))
    assert len(content) == 5
    assert set(content[0]) == {"statistic", "q05", "median", "q95", "model", "percentile"}
