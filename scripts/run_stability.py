"""Measure the stability of the six statistics across contiguous blocks.

Examples
--------
python scripts/run_stability.py --results results --blocks 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config, load_series_csv  # noqa: E402
from market_sim.stability import (  # noqa: E402
    block_metrics,
    format_stability_markdown,
    summarize_blocks,
    write_stability_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "baseline.json")
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument("--blocks", type=int, default=10)
    parser.add_argument("--report", type=Path, default=ROOT / "docs" / "stability.md")
    parser.add_argument("--csv", type=Path, default=ROOT / "docs" / "stability.csv")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    data = load_series_csv(args.results / "series.csv")
    blocks = block_metrics(data["return"], data["volume"], config.metrics, n_blocks=args.blocks)
    summary = summarize_blocks(blocks, config.metrics)
    write_stability_csv(blocks, args.csv)

    table = format_stability_markdown(blocks, config.metrics)
    all_rows = all(row["passes"] == row["total"] for row in summary.values())
    lines = [
        "# Block stability",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/run_stability.py --config {display_path(args.config)} "
            f"--results {display_path(args.results)} --blocks {args.blocks}"
        ),
        "```",
        "",
        f"- Observations: {len(data['return'])}",
        f"- Blocks: {args.blocks}",
        f"- Every statistic passes its criterion in every block: {'yes' if all_rows else 'no'}",
        "",
        table,
        "",
        "## Reading",
        "",
        "Each block is a contiguous slice of the same simulated series.  The",
        "statistics are recomputed inside the block, so the table shows whether",
        "the full-sample result comes from the whole window or from one episode.",
        "Kurtosis is the least stable statistic because it is driven by the",
        "largest returns.  The block table is descriptive and is not used as a",
        "target fact.  The cross-seed version is in `docs/block_ensemble.md`.",
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
