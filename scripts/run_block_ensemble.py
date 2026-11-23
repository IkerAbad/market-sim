"""Block stability of the six statistics across several seeds.

Examples
--------
python scripts/run_block_ensemble.py --seeds 1001-1020 --blocks 10 --jobs 8
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config  # noqa: E402
from market_sim.block_ensemble import (  # noqa: E402
    format_block_ensemble_markdown,
    run_block_ensemble,
    summarize_block_ensemble,
    write_block_ensemble_csv,
)
from market_sim.ensemble import parse_seeds  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "baseline.json")
    parser.add_argument("--seeds", default="1001-1020")
    parser.add_argument("--blocks", type=int, default=10)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--report", type=Path, default=ROOT / "docs" / "block_ensemble.md")
    parser.add_argument("--csv", type=Path, default=ROOT / "docs" / "block_ensemble.csv")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    seeds = parse_seeds(args.seeds)
    results = run_block_ensemble(config, seeds, n_blocks=args.blocks, jobs=args.jobs)
    summary = summarize_block_ensemble(results, config.metrics)
    write_block_ensemble_csv(results, config.metrics, args.csv)

    table = format_block_ensemble_markdown(results, config.metrics)
    lines = [
        "# Block stability across seeds",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/run_block_ensemble.py --config {display_path(args.config)} "
            f"--seeds {args.seeds} --blocks {args.blocks} --jobs {args.jobs}"
        ),
        "```",
        "",
        f"- Seeds: {summary.n_seeds}",
        f"- Blocks per seed: {summary.n_blocks}",
        f"- Total blocks: {summary.n_seeds * summary.n_blocks}",
        (
            f"- Seeds with every block passing all six statistics: "
            f"{summary.seed_all_blocks}/{summary.n_seeds}"
        ),
        "",
        table,
        "",
        "## Reading",
        "",
        "This table extends `docs/stability.md` from one seed to the full seed",
        "set.  Each block is a contiguous slice of one simulated series, so the",
        "block pass rate measures stability inside a run as well as across runs.",
        "The per-statistic rate counts every block of every seed.  The per-seed",
        "table counts how many blocks of that seed pass all six statistics.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")

    print(table)
    print()
    print(f"report: {args.report}")
    print(f"csv:    {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
