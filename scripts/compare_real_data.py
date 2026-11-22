"""Compare the model with a user-supplied return or price series.

Examples
--------
python scripts/compare_real_data.py --csv returns.csv --column return \
    --config configs/baseline.json --results results --report docs/real_data.md
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config, load_series_csv  # noqa: E402
from market_sim.real_data import (  # noqa: E402
    compare_metrics,
    format_comparison_markdown,
    load_returns_csv,
    write_comparison_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True, help="CSV with the data")
    parser.add_argument("--column", default="return")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline.json",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=ROOT / "results",
        help="directory containing the model series.csv",
    )
    parser.add_argument(
        "--acf-lags",
        type=int,
        default=None,
        help="optional acf_lags override for short data series",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "real_data.md",
    )
    parser.add_argument(
        "--csv-report",
        type=Path,
        default=ROOT / "docs" / "real_data.csv",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    params = (
        replace(config.metrics, acf_lags=args.acf_lags)
        if args.acf_lags is not None
        else config.metrics
    )
    model_data = load_series_csv(args.results / "series.csv")
    data_returns = load_returns_csv(args.csv, column=args.column)
    rows = compare_metrics(model_data["return"], data_returns, params)
    table = format_comparison_markdown(rows)
    write_comparison_csv(rows, args.csv_report)

    lines = [
        "# Model versus supplied data",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/compare_real_data.py --csv {args.csv.as_posix()} "
            f"--column {args.column} --config {args.config.as_posix()} "
            f"--results {args.results.as_posix()}"
        ),
        "```",
        "",
        f"- Data file: `{args.csv.as_posix()}`",
        f"- Column: `{args.column}`",
        f"- Data observations: {len(data_returns)}",
        "- The model row is the baseline series in `results/series.csv`.",
        "- The table uses the five price facts.  Volume is omitted because the",
        "  supplied data may not have a volume column.",
        "",
        table,
        "",
        "## Reading",
        "",
        "This is a diagnostic comparison, not a calibration.  The model is not",
        "fitted to the supplied series.  The data are not committed to the",
        "repository.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")

    print(table)
    print()
    print(f"report: {args.report}")
    print(f"csv:    {args.csv_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
