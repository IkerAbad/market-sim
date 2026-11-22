"""Time the simulation loop at several lengths.

Examples
--------
python scripts/run_benchmark.py --config configs/baseline.json --steps 10000,50000,100000
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config  # noqa: E402
from market_sim.benchmark import BenchmarkResult, time_simulation  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline.json",
    )
    parser.add_argument("--steps", default="10000,50000,100000")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "performance.md",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "docs" / "performance.csv",
    )
    return parser.parse_args()


def parse_steps(spec: str) -> list[int]:
    values: list[int] = []
    for token in spec.split(","):
        text = token.strip()
        if not text:
            continue
        value = int(text)
        if value < 1:
            raise ValueError("steps must be positive")
        values.append(value)
    if not values:
        raise ValueError("at least one step count is required")
    return values


def format_table(results: list[BenchmarkResult]) -> str:
    lines = [
        "| Steps | Runs | Best time (s) | Mean time (s) | Steps/s | Agent-steps/s |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            f"| {result.steps} | {result.runs} | {result.best_seconds:.3f} | "
            f"{result.mean_seconds:.3f} | {result.steps_per_second:,.0f} | "
            f"{result.agent_steps_per_second:,.0f} |"
        )
    return "\n".join(lines)


def write_csv(results: list[BenchmarkResult], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "steps",
                "runs",
                "n_agents",
                "best_seconds",
                "mean_seconds",
                "steps_per_second",
                "agent_steps_per_second",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result.steps,
                    result.runs,
                    result.n_agents,
                    f"{result.best_seconds:.10g}",
                    f"{result.mean_seconds:.10g}",
                    f"{result.steps_per_second:.10g}",
                    f"{result.agent_steps_per_second:.10g}",
                ]
            )
    return path


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    steps = parse_steps(args.steps)
    if args.repeat < 1:
        raise SystemExit("--repeat must be positive")
    results = [time_simulation(config, value, repeat=args.repeat) for value in steps]
    write_csv(results, args.csv)

    lines = [
        "# Performance",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/run_benchmark.py --config {args.config.as_posix()} "
            f"--steps {args.steps} --repeat {args.repeat}"
        ),
        "```",
        "",
        "- Reference machine: Ryzen 9 5900X, 32 GB DDR4-3600, Windows 11.",
        "- Timing includes only the simulation loop, not metrics, figures or bootstrap.",
        "",
        format_table(results),
        "",
        "## Reading",
        "",
        "The 100,000-step row is the size of the baseline run.  The table is a",
        "rough measure of how long a full configuration takes on the reference",
        "machine.  It is not a performance guarantee for other hardware.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")

    print(format_table(results))
    print()
    print(f"report: {args.report}")
    print(f"csv:    {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
