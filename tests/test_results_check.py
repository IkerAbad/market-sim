from __future__ import annotations

import json
from pathlib import Path

import pytest

from market_sim.results_check import check_results, load_baseline, parse_main_table

ROOT = Path(__file__).resolve().parents[1]

METRICS = {
    "kurtosis": 5.0,
    "acf_return_lag1": 0.0,
    "acf_abs_return_lag1": 0.2,
    "acf_abs_return_lag50": 0.1,
    "corr_volume_abs_return": 0.5,
    "tail_exceedance_ratio": 10.0,
}

TABLE = """## Results

| Fact | Statistic | Value | Criterion | Pass |
| ---: | --- | ---: | --- | :---: |
| 1 | Kurtosis | 5.0 | > 3 | yes |
| 2 | ACF(returns, lag 1) | 0.0 | abs < 0.05 | yes |
| 3 | ACF(abs(returns), lag 1) | 0.2 | > 0.05 | yes |
| 3 | ACF(abs(returns), lag 50) | 0.1 | > 0.02 | yes |
| 4 | corr(volume, abs(returns)) | 0.5 | > 0.2 | yes |
| 5 | P(abs(r) > 4 sd) / P_normal | 10.0 | > 1 | yes |

### Reading the table
"""


def _make_repo(tmp_path: Path, table: str = TABLE, facts: int = 6) -> Path:
    (tmp_path / "docs").mkdir()
    payload = {
        "metrics": METRICS,
        "facts": [{"passes": True} for _ in range(facts)],
    }
    (tmp_path / "docs" / "baseline_metrics.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "README.md").write_text(f"# Test\n\n{table}", encoding="utf-8")
    return tmp_path


def test_repository_results_table_matches() -> None:
    assert check_results(ROOT) == []


def test_valid_fixture_matches(tmp_path) -> None:
    assert check_results(_make_repo(tmp_path)) == []


def test_mismatch_is_reported(tmp_path) -> None:
    repo = _make_repo(tmp_path, TABLE.replace("| 5.0 |", "| 9.0 |"))
    errors = check_results(repo)
    assert any("Kurtosis" in error for error in errors)


def test_pass_mismatch_is_reported(tmp_path) -> None:
    repo = _make_repo(tmp_path, TABLE.replace("| > 3 | yes |", "| > 3 | no |"))
    errors = check_results(repo)
    assert any("pass is" in error for error in errors)


def test_row_count_mismatch_is_reported(tmp_path) -> None:
    repo = _make_repo(tmp_path, facts=7)
    errors = check_results(repo)
    assert any("7 rows" in error or "6 rows" in error for error in errors)


def test_unknown_statistic_is_reported(tmp_path) -> None:
    repo = _make_repo(tmp_path, TABLE.replace("Kurtosis", "Skewness"))
    errors = check_results(repo)
    assert any("unknown statistic" in error for error in errors)


def test_non_numeric_value_is_reported(tmp_path) -> None:
    repo = _make_repo(tmp_path, TABLE.replace("| 5.0 |", "| high |"))
    errors = check_results(repo)
    assert any("not numeric" in error for error in errors)


def test_missing_results_section_is_reported() -> None:
    with pytest.raises(ValueError):
        parse_main_table("# Test\n")


def test_baseline_must_be_an_object(tmp_path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "baseline_metrics.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        load_baseline(tmp_path)


def test_short_rows_are_ignored() -> None:
    rows = parse_main_table("## Results\n\n| a | b |\n| --- | --- |\n")
    assert rows == []
