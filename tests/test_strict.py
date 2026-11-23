from __future__ import annotations

import csv

import pytest

from market_sim.config import MetricsParams
from market_sim.strict import (
    evaluate_strict,
    format_strict_markdown,
    load_seed_metrics,
    write_strict_csv,
)

PARAMS = MetricsParams(
    acf_lags=50,
    kurtosis_threshold=5.0,
    tail_ratio_threshold=10.0,
)


def make_row(
    seed: int,
    kurtosis: float = 6.0,
    acf_return: float = 0.0,
    acf_abs1: float = 0.2,
    acf_abs50: float = 0.1,
    tail: float = 20.0,
) -> dict[str, float]:
    return {
        "seed": float(seed),
        "kurtosis": kurtosis,
        "acf_return_lag1": acf_return,
        "acf_abs_return_lag1": acf_abs1,
        "acf_abs_return_lag50": acf_abs50,
        "tail_exceedance_ratio": tail,
    }


def test_evaluate_strict_counts_and_failures() -> None:
    rows = [
        make_row(1),
        make_row(2, kurtosis=4.5),
        make_row(3, tail=5.0),
    ]
    summary = evaluate_strict(rows, PARAMS)
    assert summary.n_seeds == 3
    assert summary.all_pass == 1
    assert [fact.passes for fact in summary.facts] == [2, 3, 3, 3, 2]
    assert [failure.seed for failure in summary.failures] == [2, 3]
    assert summary.failures[0].failing == ("Kurtosis",)
    assert summary.failures[1].failing == ("Tail ratio",)
    assert summary.facts[0].rate == pytest.approx(2 / 3)
    assert 0.0 <= summary.all_lower <= summary.all_upper <= 1.0


def test_empty_rows_are_rejected() -> None:
    with pytest.raises(ValueError):
        evaluate_strict([], PARAMS)


def test_load_seed_metrics(tmp_path) -> None:
    path = tmp_path / "metrics.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "seed",
                "kurtosis",
                "acf_return_lag1",
                "acf_abs_return_lag1",
                "acf_abs_return_lag50",
                "tail_exceedance_ratio",
            ]
        )
        writer.writerow([1, 6.0, 0.0, 0.2, 0.1, 20.0])
    rows = load_seed_metrics(path)
    assert rows == [make_row(1)]


def test_load_seed_metrics_rejects_missing_columns(tmp_path) -> None:
    path = tmp_path / "metrics.csv"
    path.write_text("seed,kurtosis\n1,5\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_seed_metrics(path)


def test_load_seed_metrics_rejects_empty(tmp_path) -> None:
    path = tmp_path / "metrics.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError):
        load_seed_metrics(path)


def test_load_seed_metrics_rejects_empty_rows(tmp_path) -> None:
    path = tmp_path / "metrics.csv"
    path.write_text(
        "seed,kurtosis,acf_return_lag1,acf_abs_return_lag1,"
        "acf_abs_return_lag50,tail_exceedance_ratio\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_seed_metrics(path)


def test_format_strict_markdown() -> None:
    rows = [make_row(1), make_row(2, kurtosis=4.5)]
    summary = evaluate_strict(rows, PARAMS)
    markdown = format_strict_markdown(summary)
    assert "| Fact | Criterion | Passes | 95% CI |" in markdown
    assert "| Kurtosis | > 5 | 1/2 |" in markdown
    assert "| 2 | Kurtosis | 4.5 | 20 |" in markdown


def test_format_strict_markdown_without_failures() -> None:
    summary = evaluate_strict([make_row(1)], PARAMS)
    markdown = format_strict_markdown(summary)
    assert "No seed fails the strict criteria." in markdown


def test_write_strict_csv(tmp_path) -> None:
    rows = [make_row(1), make_row(2, kurtosis=4.5)]
    path = write_strict_csv(rows, PARAMS, tmp_path / "strict.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        content = list(csv.DictReader(handle))
    assert len(content) == 2
    assert content[0]["all_pass"] == "1"
    assert content[1]["all_pass"] == "0"
    assert content[1]["pass_count"] == "4"
