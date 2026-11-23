from __future__ import annotations

import sys

from market_sim.reproduce import full_commands, run_commands


def test_full_commands_cover_the_scripts() -> None:
    commands = full_commands(jobs=2)
    text = "\n".join(" ".join(command) for command in commands)
    for script in (
        "run_simulation.py",
        "make_figures.py",
        "run_ensemble.py",
        "run_inference.py",
        "run_phase_diagram.py",
        "run_ablations.py",
        "run_sensitivity_full.py",
        "run_thresholds.py",
        "run_extra_facts.py",
        "run_benchmarks.py",
        "run_benchmark.py",
        "run_sample_size.py",
        "run_price_volume.py",
        "run_stability.py",
    ):
        assert script in text
    assert "--jobs 2" in text


def test_skip_50_seeds() -> None:
    commands = full_commands(include_50_seeds=False)
    text = "\n".join(" ".join(command) for command in commands)
    assert "1001-1050" not in text


def test_dry_run_does_not_execute(capsys) -> None:
    commands = [[sys.executable, "-c", "raise SystemExit(1)"]]
    assert run_commands(commands, dry_run=True) == 0
    output = capsys.readouterr().out
    assert "$" in output


def test_run_commands_executes() -> None:
    assert run_commands([[sys.executable, "-c", "pass"]], dry_run=False) == 0
