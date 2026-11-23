"""One-command reproduction of every committed analysis."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence


def full_commands(jobs: int = 8, include_50_seeds: bool = True) -> list[list[str]]:
    """Return the ordered list of commands for a full reproduction."""
    python = sys.executable
    commands: list[list[str]] = [
        [
            python,
            "scripts/run_simulation.py",
            "--config",
            "configs/baseline.json",
            "--output",
            "results",
        ],
        [python, "scripts/make_figures.py", "--results", "results", "--output", "docs"],
        [
            python,
            "scripts/run_ensemble.py",
            "--config",
            "configs/baseline.json",
            "--seeds",
            "1001-1020",
            "--jobs",
            str(jobs),
            "--output",
            "results_ensemble",
            "--report",
            "docs/robustness.md",
        ],
    ]
    if include_50_seeds:
        commands.append(
            [
                python,
                "scripts/run_ensemble.py",
                "--config",
                "configs/baseline.json",
                "--seeds",
                "1001-1050",
                "--jobs",
                str(jobs),
                "--output",
                "results_ensemble_50",
                "--report",
                "docs/robustness_50.md",
                "--csv-report",
                "docs/robustness_50.csv",
            ]
        )
    commands.extend(
        [
            [
                python,
                "scripts/run_inference.py",
                "--config",
                "configs/baseline.json",
                "--results",
                "results",
                "--report",
                "docs/inference.md",
            ],
            [
                python,
                "scripts/run_phase_diagram.py",
                "--config",
                "configs/baseline.json",
                "--seeds",
                "1-3",
                "--jobs",
                str(jobs),
            ],
            [
                python,
                "scripts/run_ablations.py",
                "--config",
                "configs/baseline.json",
                "--seeds",
                "1001-1003",
                "--jobs",
                str(jobs),
            ],
            [
                python,
                "scripts/run_sensitivity_full.py",
                "--config",
                "configs/baseline.json",
                "--seeds",
                "1001-1003",
                "--jobs",
                str(jobs),
            ],
            [
                python,
                "scripts/run_thresholds.py",
                "--input",
                "docs/robustness.csv",
                "--report",
                "docs/thresholds.md",
            ],
            [
                python,
                "scripts/run_extra_facts.py",
                "--results",
                "results",
                "--report",
                "docs/additional_facts.md",
            ],
            [
                python,
                "scripts/run_benchmarks.py",
                "--config",
                "configs/baseline.json",
                "--results",
                "results",
                "--report",
                "docs/benchmarks.md",
            ],
            [
                python,
                "scripts/run_benchmark_rates.py",
                "--config",
                "configs/baseline.json",
                "--series",
                "100",
                "--n",
                "100000",
            ],
            [
                python,
                "scripts/run_strict_criteria.py",
                "--config",
                "configs/baseline.json",
                "--input",
                "docs/robustness_50.csv",
            ],
            [
                python,
                "scripts/run_null_distribution.py",
                "--config",
                "configs/baseline.json",
                "--series",
                "1000",
                "--n",
                "100000",
            ],
            [
                python,
                "scripts/run_discrimination.py",
                "--config",
                "configs/baseline.json",
                "--series",
                "100",
                "--n",
                "100000",
            ],
            [
                python,
                "scripts/run_benchmark.py",
                "--config",
                "configs/baseline.json",
                "--steps",
                "10000,50000,100000",
            ],
            [
                python,
                "scripts/run_sample_size.py",
                "--config",
                "configs/baseline.json",
                "--seeds",
                "1001-1003",
                "--jobs",
                str(jobs),
            ],
            [
                python,
                "scripts/run_price_volume.py",
                "--config",
                "configs/baseline.json",
                "--results",
                "results",
                "--report",
                "docs/price_volume.md",
            ],
            [
                python,
                "scripts/run_stability.py",
                "--config",
                "configs/baseline.json",
                "--results",
                "results",
                "--blocks",
                "10",
            ],
            [
                python,
                "scripts/run_block_ensemble.py",
                "--config",
                "configs/baseline.json",
                "--seeds",
                "1001-1020",
                "--blocks",
                "10",
                "--jobs",
                str(jobs),
            ],
        ]
    )
    return commands


def run_commands(commands: Sequence[Sequence[str]], dry_run: bool = False) -> int:
    """Run each command in order and return the last exit code."""
    for command in commands:
        print("$", " ".join(command))
        if dry_run:
            continue
        subprocess.run(list(command), check=True)
    return 0
