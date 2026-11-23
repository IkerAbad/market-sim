"""Run the finite-sample sensitivity study.

Examples
--------
python scripts/run_sample_size.py --config configs/baseline.json \
    --sizes 10000,50000,100000,200000 --seeds 1001-1003 --jobs 8
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config  # noqa: E402
from market_sim.ensemble import parse_seeds  # noqa: E402
from market_sim.sample_size import (  # noqa: E402
    format_sample_size_markdown,
    run_sample_size_grid,
    sample_size_report,
    summarize_sample_size,
    write_sample_size_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline.json",
    )
    parser.add_argument("--sizes", default="10000,50000,100000,200000")
    parser.add_argument("--seeds", default="1001-1003")
    parser.add_argument(
        "--jobs",
        type=int,
        default=0,
        help="worker processes, 0 means min(8, CPU count)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "sample_size.md",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "docs" / "sample_size.csv",
    )
    return parser.parse_args()


def parse_sizes(spec: str) -> list[int]:
    values: list[int] = []
    for token in spec.split(","):
        text = token.strip()
        if not text:
            continue
        value = int(text)
        if value < 2:
            raise ValueError("sizes must be at least 2")
        values.append(value)
    if not values:
        raise ValueError("at least one size is required")
    return values


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    sizes = parse_sizes(args.sizes)
    seeds = parse_seeds(args.seeds)
    jobs = args.jobs if args.jobs > 0 else min(8, os.cpu_count() or 1)
    print(f"running {len(sizes)} sizes x {len(seeds)} seeds with {jobs} worker(s)")
    results = run_sample_size_grid(config, sizes, seeds, jobs=jobs)
    summary = summarize_sample_size(results)
    write_sample_size_csv(results, args.csv)

    command = (
        f"python scripts/run_sample_size.py --config {args.config.as_posix()} "
        f"--sizes {args.sizes} --seeds {args.seeds} --jobs {jobs}"
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(sample_size_report(summary, command), encoding="utf-8")

    print(format_sample_size_markdown(summary))
    print()
    print(f"report: {args.report}")
    print(f"csv:    {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
