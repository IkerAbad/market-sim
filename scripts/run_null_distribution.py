"""Percentiles of the five price statistics under Gaussian noise.

Examples
--------
python scripts/run_null_distribution.py --series 1000 --n 100000
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config  # noqa: E402
from market_sim.null_distribution import (  # noqa: E402
    format_null_markdown,
    null_statistics,
    write_null_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "baseline.json")
    parser.add_argument("--metrics", type=Path, default=ROOT / "docs" / "baseline_metrics.json")
    parser.add_argument("--series", type=int, default=1000)
    parser.add_argument("--n", type=int, default=100000)
    parser.add_argument("--report", type=Path, default=ROOT / "docs" / "null_distribution.md")
    parser.add_argument("--csv", type=Path, default=ROOT / "docs" / "null_distribution.csv")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    params = replace(config.metrics, acf_lags=50)
    data = json.loads(args.metrics.read_text(encoding="utf-8"))
    model_metrics = data["metrics"]
    rows = null_statistics(
        params,
        model_metrics,
        n_series=args.series,
        n=args.n,
    )
    write_null_csv(rows, args.csv)
    table = format_null_markdown(rows)

    lines = [
        "# Null distribution under Gaussian noise",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/run_null_distribution.py --config {display_path(args.config)} "
            f"--series {args.series} --n {args.n}"
        ),
        "```",
        "",
        f"- Gaussian series: {args.series}",
        f"- Observations per series: {args.n}",
        "- ACF computed up to lag 50",
        f"- Model metrics: `{display_path(args.metrics)}`",
        "",
        table,
        "",
        "## Reading",
        "",
        "The 5% and 95% columns are the quantiles of each statistic over",
        "independent Gaussian series of the same length.  The last column is the",
        "fraction of Gaussian series below the model value.",
        "",
        "The kurtosis threshold of 3 sits at the median of the Gaussian null, so",
        "about half of Gaussian samples pass it.  The model value 5.488 is far",
        "outside the 95% quantile.  The same happens with the tail ratio.  The",
        "return autocorrelation is small in magnitude, near the 5% quantile of",
        "the Gaussian null, as intended.  The absolute-return autocorrelations",
        "are far above the Gaussian 95% quantile, which is the part of the table",
        "that the benchmarks do not reproduce with a simple Gaussian process.",
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
