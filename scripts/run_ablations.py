"""Run the component ablation study.

Examples
--------
python scripts/run_ablations.py --config configs/baseline.json --seeds 1001-1003 --jobs 8
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config  # noqa: E402
from market_sim.ablations import (  # noqa: E402
    ABLATIONS,
    ablation_report,
    run_ablation_grid,
    summarize_ablations,
    write_ablation_csv,
)
from market_sim.ensemble import parse_seeds  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline.json",
    )
    parser.add_argument("--seeds", default="1001-1003")
    parser.add_argument("--steps", type=int, default=101000)
    parser.add_argument("--burn-in", type=int, default=1000)
    parser.add_argument(
        "--jobs",
        type=int,
        default=0,
        help="worker processes, 0 means min(8, CPU count)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "ablations.md",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "docs" / "ablations.csv",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base = load_config(args.config)
    config = replace(base, n_steps=args.steps, burn_in=args.burn_in)
    seeds = parse_seeds(args.seeds)
    jobs = args.jobs if args.jobs > 0 else min(8, os.cpu_count() or 1)
    print(f"running {len(ABLATIONS)} ablations x {len(seeds)} seeds with {jobs} worker(s)")
    results = run_ablation_grid(config, ABLATIONS, seeds, jobs=jobs)
    summary = summarize_ablations(results, ABLATIONS)
    write_ablation_csv(results, args.csv)

    command = (
        f"python scripts/run_ablations.py --config {args.config.as_posix()} "
        f"--seeds {args.seeds} --steps {args.steps} --burn-in {args.burn_in} "
        f"--jobs {jobs}"
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(ablation_report(summary, command), encoding="utf-8")

    print(ablation_report(summary, command))
    print()
    print(f"report: {args.report}")
    print(f"csv:    {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
