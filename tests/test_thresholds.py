from __future__ import annotations

import csv

import pytest

from market_sim.thresholds import (
    evaluate_thresholds,
    format_threshold_markdown,
    load_metrics_csv,
    threshold_report,
    write_threshold_csv,
)


def sample_rows() -> list[dict[str, float]]:
    return [
        {
            "kurtosis": 5.0,
            "acf_return_lag1": 0.01,
            "acf_abs_return_lag1": 0.20,
            "acf_abs_return_lag50": 0.10,
            "corr_volume_abs_return": 0.50,
            "tail_exceedance_ratio": 10.0,
        },
        {
            "kurtosis": 7.0,
            "acf_return_lag1": -0.03,
            "acf_abs_return_lag1": 0.15,
            "acf_abs_return_lag50": 0.08,
            "corr_volume_abs_return": 0.40,
            "tail_exceedance_ratio": 5.0,
        },
    ]


def test_evaluate_thresholds() -> None:
    grid = (
        ("Kurtosis", "kurtosis", ">", (6.0, 8.0)),
        ("ACF(returns, 1)", "acf_return_lag1", "abs<", (0.02, 0.05)),
    )
    rows = evaluate_thresholds(sample_rows(), grid)
    assert len(rows) == 4
    assert rows[0].passes == 1
    assert rows[1].passes == 0
    assert rows[2].passes == 1
    assert rows[3].passes == 2
    table = format_threshold_markdown(rows)
    assert "| Fact | Threshold | Seeds passing | Pass rate |" in table
    report = threshold_report(rows, "python scripts/run_thresholds.py", "input.csv")
    assert "# Threshold sensitivity" in report


def test_load_metrics_csv(tmp_path) -> None:
    columns = [
        "kurtosis",
        "acf_return_lag1",
        "acf_abs_return_lag1",
        "acf_abs_return_lag50",
        "corr_volume_abs_return",
        "tail_exceedance_ratio",
    ]
    path = tmp_path / "metrics.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerow(dict(zip(columns, [5.0, 0.01, 0.2, 0.1, 0.5, 10.0], strict=True)))
    rows = load_metrics_csv(path)
    assert len(rows) == 1
    assert rows[0]["kurtosis"] == 5.0


def test_load_metrics_csv_rejects_bad_files(tmp_path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError):
        load_metrics_csv(empty)

    missing = tmp_path / "missing.csv"
    missing.write_text("kurtosis\n5\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_metrics_csv(missing)

    no_rows = tmp_path / "no_rows.csv"
    no_rows.write_text(
        "kurtosis,acf_return_lag1,acf_abs_return_lag1,acf_abs_return_lag50,"
        "corr_volume_abs_return,tail_exceedance_ratio\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_metrics_csv(no_rows)


def test_write_threshold_csv(tmp_path) -> None:
    grid = (("Kurtosis", "kurtosis", ">", (6.0,)),)
    rows = evaluate_thresholds(sample_rows(), grid)
    path = write_threshold_csv(rows, tmp_path / "thresholds.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        content = list(csv.DictReader(handle))
    assert len(content) == 1
    assert set(content[0]) == {
        "fact",
        "column",
        "direction",
        "threshold",
        "passes",
        "total",
        "rate",
    }
