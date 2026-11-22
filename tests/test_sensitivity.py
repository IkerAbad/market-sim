from __future__ import annotations

import csv

from market_sim.ablations import write_ablation_csv
from market_sim.config import MetricsParams, ModelParams, SimulationConfig
from market_sim.sensitivity import (
    SENSITIVITY_VARIANTS,
    format_sensitivity_markdown,
    run_sensitivity_grid,
    sensitivity_report,
    summarize_sensitivity,
)


def make_config() -> SimulationConfig:
    return SimulationConfig(
        seed=1,
        n_steps=200,
        burn_in=20,
        model=ModelParams(n_agents=20, memory_min=2, memory_max=10),
        metrics=MetricsParams(acf_lags=50),
    )


def test_sensitivity_catalog() -> None:
    names = [variant.name for variant in SENSITIVITY_VARIANTS]
    assert names[0] == "baseline"
    assert len(names) == len(set(names))
    assert "activity_0.75" in names
    assert "memory_long" in names


def test_sensitivity_run_and_report(tmp_path) -> None:
    results = run_sensitivity_grid(make_config(), [1], jobs=1)
    summary = summarize_sensitivity(results)
    assert summary.n_seeds == 1
    assert len(summary.names) == len(SENSITIVITY_VARIANTS)
    table = format_sensitivity_markdown(summary)
    assert "| Variant |" in table
    report = sensitivity_report(summary, "python scripts/run_sensitivity_full.py")
    assert "# One-at-a-time sensitivity" in report
    assert "Variants with all seeds passing" in report

    path = write_ablation_csv(results, tmp_path / "sensitivity.csv", first_column="variant")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        assert reader.fieldnames[0] == "variant"
