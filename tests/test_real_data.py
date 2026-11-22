from __future__ import annotations

import csv

import numpy as np
import pytest

from market_sim.config import MetricsParams
from market_sim.real_data import (
    compare_metrics,
    format_comparison_markdown,
    load_returns_csv,
    write_comparison_csv,
)


def write_series_csv(path, returns: list[float]) -> None:
    prices = 100.0 * np.exp(np.cumsum(returns))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["return", "close"])
        for value, price in zip(returns, prices, strict=True):
            writer.writerow([f"{value:.10f}", f"{price:.10f}"])


def test_load_returns_from_return_column(tmp_path) -> None:
    values = [0.01, -0.02, 0.005, 0.0, -0.01, 0.02, 0.003, -0.004]
    path = tmp_path / "series.csv"
    write_series_csv(path, values)
    loaded = load_returns_csv(path, column="return")
    assert np.allclose(loaded, values)


def test_load_returns_from_price_column(tmp_path) -> None:
    values = [0.01, -0.02, 0.005, 0.0, -0.01, 0.02, 0.003, -0.004]
    path = tmp_path / "series.csv"
    write_series_csv(path, values)
    loaded = load_returns_csv(path, column="close")
    assert loaded.shape == (len(values) - 1,)
    assert np.allclose(loaded, np.asarray(values[1:]))


def test_load_returns_rejects_bad_files(tmp_path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError):
        load_returns_csv(empty)
    missing = tmp_path / "missing.csv"
    missing.write_text("value\n1\n2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_returns_csv(missing, column="return")
    one = tmp_path / "one.csv"
    one.write_text("return\n0.01\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_returns_csv(one)
    negative = tmp_path / "negative.csv"
    negative.write_text("close\n100\n-1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_returns_csv(negative, column="close")


def test_compare_metrics_and_outputs(tmp_path) -> None:
    rng = np.random.default_rng(1)
    model_returns = rng.normal(0.0, 0.01, size=1000)
    data_returns = rng.standard_t(5, size=1000) * 0.01
    params = MetricsParams(acf_lags=50)
    rows = compare_metrics(model_returns, data_returns, params)
    assert len(rows) == 5
    assert set(rows[0]) == {
        "statistic",
        "model",
        "data",
        "difference",
        "model_pass",
        "data_pass",
    }
    assert all(isinstance(row["model_pass"], bool) for row in rows)
    table = format_comparison_markdown(rows)
    assert "| Statistic | Model | Data | Data minus model | Model pass | Data pass |" in table
    path = write_comparison_csv(rows, tmp_path / "comparison.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        content = list(csv.DictReader(handle))
    assert len(content) == 5
    assert set(content[0]) == {
        "statistic",
        "model",
        "data",
        "difference",
        "model_pass",
        "data_pass",
    }
