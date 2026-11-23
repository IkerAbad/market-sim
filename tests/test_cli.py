from __future__ import annotations

import json
from pathlib import Path

import pytest

from market_sim.cli import ensemble_main, figures_main, main, simulate_main
from market_sim.config import config_to_dict, load_config

ROOT = Path(__file__).resolve().parents[1]


def write_small_config(tmp_path: Path) -> Path:
    data = config_to_dict(load_config(ROOT / "configs" / "baseline.json"))
    data["n_steps"] = 120
    data["burn_in"] = 10
    data["model"]["n_agents"] = 20
    data["model"]["memory_min"] = 2
    data["model"]["memory_max"] = 10
    data["metrics"]["acf_lags"] = 50
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_version(capsys) -> None:
    assert main(["version"]) == 0
    assert "0.4.1" in capsys.readouterr().out


def test_simulate_cli(tmp_path) -> None:
    config = write_small_config(tmp_path)
    output = tmp_path / "results"
    assert (
        simulate_main(
            [
                "--config",
                str(config),
                "--output",
                str(output),
                "--seed",
                "5",
                "--set",
                "n_steps=120",
            ]
        )
        == 0
    )
    assert (output / "series.csv").exists()
    assert (output / "metrics.json").exists()
    assert (output / "config.json").exists()
    assert (output / "results.md").exists()
    metrics = json.loads((output / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["seed"] == 5
    assert metrics["n_steps"] == 120


def test_main_dispatches_simulate(tmp_path) -> None:
    config = write_small_config(tmp_path)
    output = tmp_path / "results"
    assert main(["simulate", "--config", str(config), "--output", str(output)]) == 0
    assert (output / "series.csv").exists()


def test_figures_cli(tmp_path) -> None:
    config = write_small_config(tmp_path)
    results = tmp_path / "results"
    figures = tmp_path / "figures"
    assert simulate_main(["--config", str(config), "--output", str(results)]) == 0
    assert (
        figures_main(
            [
                "--config",
                str(config),
                "--results",
                str(results),
                "--output",
                str(figures),
                "--max-lag",
                "20",
            ]
        )
        == 0
    )
    assert (figures / "price_series.png").exists()
    assert (figures / "return_histogram.png").exists()
    assert (figures / "autocorrelation.png").exists()


def test_figures_without_saved_series(tmp_path) -> None:
    config = write_small_config(tmp_path)
    figures = tmp_path / "figures"
    assert (
        figures_main(
            [
                "--config",
                str(config),
                "--results",
                str(tmp_path / "missing"),
                "--output",
                str(figures),
                "--max-lag",
                "20",
            ]
        )
        == 0
    )
    assert (figures / "autocorrelation.png").exists()


def test_ensemble_cli(tmp_path) -> None:
    config = write_small_config(tmp_path)
    output = tmp_path / "ensemble"
    report = tmp_path / "robustness.md"
    csv_report = tmp_path / "robustness.csv"
    assert (
        ensemble_main(
            [
                "--config",
                str(config),
                "--seeds",
                "1-2",
                "--jobs",
                "1",
                "--output",
                str(output),
                "--report",
                str(report),
                "--csv-report",
                str(csv_report),
            ]
        )
        == 0
    )
    assert (output / "metrics.csv").exists()
    assert (output / "summary.json").exists()
    assert report.exists()
    assert csv_report.exists()
    assert "Robustness across seeds" in report.read_text(encoding="utf-8")


def test_invalid_override_exits(tmp_path) -> None:
    config = write_small_config(tmp_path)
    with pytest.raises(SystemExit) as exc:
        simulate_main(["--config", str(config), "--set", "not-an-override"])
    assert exc.value.code == 2


def test_simulate_bad_config_exits(tmp_path) -> None:
    with pytest.raises(SystemExit) as exc:
        simulate_main(["--config", str(tmp_path / "missing.json")])
    assert exc.value.code == 2


def test_figures_bad_config_exits(tmp_path) -> None:
    with pytest.raises(SystemExit) as exc:
        figures_main(["--config", str(tmp_path / "missing.json")])
    assert exc.value.code == 2


def test_ensemble_bad_seeds_exits(tmp_path) -> None:
    config = write_small_config(tmp_path)
    with pytest.raises(SystemExit) as exc:
        ensemble_main(["--config", str(config), "--seeds", "not-a-seed"])
    assert exc.value.code == 2


def test_main_figures_dispatch(tmp_path) -> None:
    config = write_small_config(tmp_path)
    results = tmp_path / "results"
    figures = tmp_path / "figures"
    assert simulate_main(["--config", str(config), "--output", str(results)]) == 0
    assert (
        main(
            [
                "figures",
                "--config",
                str(config),
                "--results",
                str(results),
                "--output",
                str(figures),
                "--max-lag",
                "20",
            ]
        )
        == 0
    )
    assert (figures / "price_series.png").exists()


def test_main_ensemble_dispatch(tmp_path) -> None:
    config = write_small_config(tmp_path)
    assert (
        main(
            [
                "ensemble",
                "--config",
                str(config),
                "--seeds",
                "1-2",
                "--jobs",
                "1",
                "--output",
                str(tmp_path / "ensemble"),
                "--report",
                str(tmp_path / "robustness.md"),
                "--csv-report",
                str(tmp_path / "robustness.csv"),
            ]
        )
        == 0
    )


def test_main_error_exits(tmp_path) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["simulate", "--config", str(tmp_path / "missing.json")])
    assert exc.value.code == 2


def test_main_requires_command() -> None:
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_python_module_entrypoint(monkeypatch, capsys) -> None:
    import runpy
    import sys

    monkeypatch.setattr(sys, "argv", ["market-sim", "version"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("market_sim", run_name="__main__")
    assert exc.value.code == 0
    assert "0.4.1" in capsys.readouterr().out
