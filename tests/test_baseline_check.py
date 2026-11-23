from __future__ import annotations

import json

import pytest

from market_sim.baseline_check import compare_baseline, compare_summaries, load_summary

SUMMARY = {
    "metrics": {
        "n_observations": 100000,
        "kurtosis": 5.488,
        "acf_return_lag1": -0.004945,
    },
    "facts": [
        {"statistic": "Kurtosis", "passes": True},
        {"statistic": "ACF(returns, lag 1)", "passes": True},
    ],
    "all_facts_pass": True,
}


def test_identical_summaries_pass() -> None:
    assert compare_summaries(SUMMARY, SUMMARY) == []


def test_metric_mismatch_is_reported() -> None:
    actual = json.loads(json.dumps(SUMMARY))
    actual["metrics"]["kurtosis"] = 5.5
    errors = compare_summaries(SUMMARY, actual)
    assert any("kurtosis" in error for error in errors)


def test_missing_metric_is_reported() -> None:
    actual = json.loads(json.dumps(SUMMARY))
    del actual["metrics"]["kurtosis"]
    errors = compare_summaries(SUMMARY, actual)
    assert any("missing" in error for error in errors)


def test_integer_metric_mismatch_is_reported() -> None:
    actual = json.loads(json.dumps(SUMMARY))
    actual["metrics"]["n_observations"] = 99999
    errors = compare_summaries(SUMMARY, actual)
    assert any("n_observations" in error for error in errors)


def test_missing_fact_is_reported() -> None:
    actual = json.loads(json.dumps(SUMMARY))
    actual["facts"] = actual["facts"][:1]
    errors = compare_summaries(SUMMARY, actual)
    assert any("missing" in error for error in errors)


def test_fact_mismatch_is_reported() -> None:
    actual = json.loads(json.dumps(SUMMARY))
    actual["facts"][0]["passes"] = False
    errors = compare_summaries(SUMMARY, actual)
    assert any("Kurtosis" in error for error in errors)


def test_all_facts_flag_mismatch_is_reported() -> None:
    actual = json.loads(json.dumps(SUMMARY))
    actual["all_facts_pass"] = False
    errors = compare_summaries(SUMMARY, actual)
    assert any("all_facts_pass" in error for error in errors)


def test_load_summary_rejects_bad_files(tmp_path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        load_summary(bad)
    missing = tmp_path / "missing.json"
    missing.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        load_summary(missing)


def test_compare_baseline(tmp_path) -> None:
    results = tmp_path / "results"
    results.mkdir()
    (results / "metrics.json").write_text(json.dumps(SUMMARY), encoding="utf-8")
    expected = tmp_path / "expected.json"
    expected.write_text(json.dumps(SUMMARY), encoding="utf-8")
    assert compare_baseline(results, expected) == []
