from __future__ import annotations

import csv

import pytest

from market_sim.config import MetricsParams
from market_sim.discrimination import (
    FACT_DIRECTIONS,
    auc,
    bootstrap_auc_interval,
    discrimination_rows,
    format_discrimination_markdown,
    format_grid_markdown,
    plot_threshold_grid,
    threshold_grid,
    write_discrimination_csv,
    write_grid_csv,
)

PARAMS = MetricsParams(acf_lags=50)


def make_row(
    kurtosis: float,
    acf_return: float = 0.0,
    acf_abs1: float = 0.2,
    acf_abs50: float = 0.1,
    tail: float = 20.0,
) -> dict[str, float]:
    return {
        "kurtosis": kurtosis,
        "acf_return_lag1": acf_return,
        "acf_abs_return_lag1": acf_abs1,
        "acf_abs_return_lag50": acf_abs50,
        "tail_exceedance_ratio": tail,
    }


def test_auc() -> None:
    assert auc([2.0, 3.0], [1.0, 2.0], higher_is_better=True) == pytest.approx(0.875)
    assert auc([2.0, 3.0], [1.0, 2.0], higher_is_better=False) == pytest.approx(0.125)
    assert auc([1.0], [1.0]) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        auc([], [1.0])


def test_bootstrap_auc_interval() -> None:
    lower, upper = bootstrap_auc_interval(
        [2.0, 3.0, 4.0],
        [1.0, 2.0, 3.0],
        higher_is_better=True,
        n_resamples=50,
    )
    assert 0.0 <= lower <= upper <= 1.0
    with pytest.raises(ValueError):
        bootstrap_auc_interval([1.0], [1.0], n_resamples=0)
    with pytest.raises(ValueError):
        bootstrap_auc_interval([], [1.0])


def test_discrimination_rows() -> None:
    model = [make_row(6.0), make_row(7.0)]
    garch = [make_row(4.0), make_row(4.5)]
    gaussian = [make_row(3.0), make_row(3.1)]
    rows = discrimination_rows(model, garch, gaussian)
    assert len(rows) == 5
    kurtosis = next(row for row in rows if row.key == "kurtosis")
    assert kurtosis.auc_garch == 1.0
    assert kurtosis.auc_gaussian == 1.0
    assert kurtosis.auc_garch_lower <= kurtosis.auc_garch <= kurtosis.auc_garch_upper
    assert kurtosis.model_median == pytest.approx(6.5)
    with pytest.raises(ValueError):
        discrimination_rows([], garch, gaussian)


def test_unknown_direction_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(FACT_DIRECTIONS, "kurtosis", "sideways")
    with pytest.raises(ValueError):
        discrimination_rows([make_row(5.0)], [make_row(4.0)], [make_row(3.0)])


def test_threshold_grid() -> None:
    model = [make_row(6.0), make_row(4.0)]
    garch = [make_row(4.0), make_row(3.5)]
    gaussian = [make_row(3.0), make_row(3.1)]
    cells = threshold_grid(
        model,
        garch,
        gaussian,
        PARAMS,
        kurtosis_thresholds=(3.0, 5.0),
        tail_thresholds=(1.0, 10.0),
    )
    assert len(cells) == 4
    strict = next(cell for cell in cells if cell.kurtosis == 5.0 and cell.tail == 10.0)
    assert strict.model_pass == 1
    assert strict.garch_pass == 0
    assert strict.gaussian_pass == 0
    with pytest.raises(ValueError):
        threshold_grid([], garch, gaussian, PARAMS)


def test_formatting_and_csv(tmp_path) -> None:
    model = [make_row(6.0), make_row(4.0)]
    garch = [make_row(4.0), make_row(3.5)]
    gaussian = [make_row(3.0), make_row(3.1)]
    rows = discrimination_rows(model, garch, gaussian)
    cells = threshold_grid(
        model,
        garch,
        gaussian,
        PARAMS,
        kurtosis_thresholds=(3.0, 5.0),
        tail_thresholds=(1.0, 10.0),
    )
    table = format_discrimination_markdown(rows)
    assert "| Statistic | Model median |" in table
    grid_table = format_grid_markdown(cells)
    assert "| Kurtosis > | Tail ratio > | Model | GARCH | Gaussian |" in grid_table

    auc_path = write_discrimination_csv(rows, tmp_path / "auc.csv")
    with auc_path.open("r", encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 5
    grid_path = write_grid_csv(cells, tmp_path / "grid.csv")
    with grid_path.open("r", encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 4


def test_plot_threshold_grid(tmp_path) -> None:
    model = [make_row(6.0), make_row(4.0)]
    garch = [make_row(4.0), make_row(3.5)]
    gaussian = [make_row(3.0), make_row(3.1)]
    cells = threshold_grid(
        model,
        garch,
        gaussian,
        PARAMS,
        kurtosis_thresholds=(3.0, 5.0),
        tail_thresholds=(1.0, 10.0),
    )
    path = plot_threshold_grid(
        cells,
        kurtosis_thresholds=(3.0, 5.0),
        tail_thresholds=(1.0, 10.0),
        path=tmp_path / "discrimination.png",
    )
    assert path.stat().st_size > 0
