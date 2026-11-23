from __future__ import annotations

from pathlib import Path

from market_sim.result_hash import (
    canonical_metrics_hash,
    combined_result_hash,
    result_hashes,
)


def make_results(
    tmp_path: Path,
    metrics: str = "{}\n",
    series: str = "step,price\n1,100\n",
) -> Path:
    results = tmp_path / "results"
    results.mkdir(parents=True)
    (results / "metrics.json").write_text(metrics, encoding="utf-8")
    (results / "series.csv").write_text(series, encoding="utf-8")
    return results


def test_result_hashes_are_stable(tmp_path) -> None:
    results = make_results(tmp_path)
    first = result_hashes(results)
    second = result_hashes(results)
    assert first == second
    assert set(first) == {"metrics", "series"}
    assert combined_result_hash(results) == combined_result_hash(results)


def test_crlf_and_lf_give_the_same_hash(tmp_path) -> None:
    lf = make_results(tmp_path / "lf")
    crlf = tmp_path / "crlf"
    crlf.mkdir()
    (crlf / "metrics.json").write_bytes(b"{}\r\n")
    (crlf / "series.csv").write_bytes(b"step,price\r\n1,100\r\n")
    assert combined_result_hash(lf) == combined_result_hash(crlf)


def test_content_change_changes_the_hash(tmp_path) -> None:
    first = make_results(tmp_path / "first")
    second = make_results(tmp_path / "second", series="step,price\n1,101\n")
    assert combined_result_hash(first) != combined_result_hash(second)


def test_canonical_metrics_round_to_six_significant_digits(tmp_path) -> None:
    first = make_results(tmp_path / "first", metrics='{"k": 5.487789}\n')
    second = make_results(tmp_path / "second", metrics='{"k": 5.487790}\n')
    third = make_results(tmp_path / "third", metrics='{"k": 5.5}\n')
    assert canonical_metrics_hash(first) == canonical_metrics_hash(second)
    assert canonical_metrics_hash(first) != canonical_metrics_hash(third)


def test_metric_formatting_does_not_change_the_hash(tmp_path) -> None:
    first = make_results(tmp_path / "first", metrics='{"a": 1.0, "b": 2.0}\n')
    second = make_results(tmp_path / "second", metrics='{"b": 2.0, "a": 1.0}\n')
    assert canonical_metrics_hash(first) == canonical_metrics_hash(second)


def test_nested_values_are_canonical(tmp_path) -> None:
    metrics = '{"a": [1.0000001, 2.0, true, "x"], "b": 3}\n'
    results = make_results(tmp_path, metrics=metrics)
    assert len(canonical_metrics_hash(results)) == 64
