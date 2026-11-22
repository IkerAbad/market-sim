"""Run a coarse parameter robustness map.

Examples
--------
python scripts/run_phase_diagram.py --seeds 1-3 --jobs 8
python scripts/run_phase_diagram.py --activity 0.8,1.0,1.2 --chartist 0.05,0.1,0.2
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")

from market_sim import load_config  # noqa: E402
from market_sim.ensemble import parse_seeds  # noqa: E402
from market_sim.phase import (  # noqa: E402
    parse_values,
    phase_report,
    plot_phase_heatmap,
    run_phase_grid,
    summarize_phase,
    write_phase_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline.json",
        help="JSON configuration file",
    )
    parser.add_argument("--activity", default="0.5,0.75,1.0,1.25,1.5")
    parser.add_argument("--chartist", default="0.05,0.1,0.2,0.5,1.0")
    parser.add_argument("--seeds", default="1-3")
    parser.add_argument("--steps", type=int, default=30000)
    parser.add_argument("--burn-in", type=int, default=1000)
    parser.add_argument(
        "--jobs",
        type=int,
        default=0,
        help="worker processes, 0 means min(8, CPU count)",
    )
    parser.add_argument(
        "--heatmap",
        type=Path,
        default=ROOT / "docs" / "phase_diagram.png",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "docs" / "phase_diagram.csv",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "phase_diagram.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base = load_config(args.config)
    config = replace(base, n_steps=args.steps, burn_in=args.burn_in)
    activity_values = parse_values(args.activity)
    chartist_values = parse_values(args.chartist)
    seeds = parse_seeds(args.seeds)
    jobs = args.jobs if args.jobs > 0 else min(8, os.cpu_count() or 1)
    print(
        f"running {len(activity_values) * len(chartist_values)} cells "
        f"x {len(seeds)} seeds with {jobs} worker(s)"
    )

    points = run_phase_grid(config, activity_values, chartist_values, seeds, jobs=jobs)
    summary = summarize_phase(points)
    write_phase_csv(points, args.csv)
    plot_phase_heatmap(summary, args.heatmap)

    command = (
        f"python scripts/run_phase_diagram.py --config {args.config.as_posix()} "
        f"--activity {args.activity} --chartist {args.chartist} "
        f"--seeds {args.seeds} --steps {args.steps} --burn-in {args.burn_in} "
        f"--jobs {jobs}"
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(phase_report(summary, command), encoding="utf-8")

    print(phase_report(summary, command))
    print()
    print(f"heatmap: {args.heatmap}")
    print(f"csv:     {args.csv}")
    print(f"report:  {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
