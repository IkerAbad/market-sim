"""Threshold sensitivity for the per-seed metrics.

Examples
--------
python scripts/run_thresholds.py --input docs/robustness.csv --report docs/thresholds.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.thresholds import (  # noqa: E402
    evaluate_thresholds,
    format_threshold_markdown,
    load_metrics_csv,
    threshold_report,
    write_threshold_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "docs" / "robustness.csv",
        help="per-seed metrics CSV",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "thresholds.md",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "docs" / "thresholds.csv",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    args = parse_args()
    rows = load_metrics_csv(args.input)
    thresholds = evaluate_thresholds(rows)
    write_threshold_csv(thresholds, args.csv)

    command = (
        f"python scripts/run_thresholds.py --input {display_path(args.input)} "
        f"--report {display_path(args.report)} --csv {display_path(args.csv)}"
    )
    report = threshold_report(thresholds, command, display_path(args.input))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")

    print(format_threshold_markdown(thresholds))
    print()
    print(f"report: {args.report}")
    print(f"csv:    {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
