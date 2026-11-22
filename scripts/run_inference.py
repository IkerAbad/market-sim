"""Bootstrap confidence intervals for the baseline statistics.

Examples
--------
python scripts/run_inference.py --results results --report docs/inference.md
python scripts/run_inference.py --resamples 500 --block-length 200
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config, load_series_csv  # noqa: E402
from market_sim.bootstrap import (  # noqa: E402
    bootstrap_metrics,
    format_bootstrap_markdown,
    write_bootstrap_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline.json",
        help="configuration with the metric thresholds",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=ROOT / "results",
        help="directory containing series.csv",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "inference.md",
        help="Markdown report path",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "docs" / "inference.csv",
        help="bootstrap summary CSV path",
    )
    parser.add_argument("--resamples", type=int, default=200)
    parser.add_argument("--block-length", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=12345)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    data = load_series_csv(args.results / "series.csv")
    result = bootstrap_metrics(
        data["return"],
        data["volume"],
        config.metrics,
        n_resamples=args.resamples,
        block_length=args.block_length,
        seed=args.seed,
    )
    table = format_bootstrap_markdown(result)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    write_bootstrap_csv(result, args.csv)

    lines = [
        "# Bootstrap intervals",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/run_inference.py --config {args.config.as_posix()} "
            f"--results {args.results.as_posix()} --resamples {result.n_resamples} "
            f"--block-length {result.block_length} --seed {result.seed}"
        ),
        "```",
        "",
        f"- Observations: {len(data['return'])}",
        f"- Bootstrap resamples: {result.n_resamples}",
        f"- Block length: {result.block_length}",
        f"- Bootstrap seed: {result.seed}",
        "",
        table,
        "",
        "## Reading",
        "",
        "The bootstrap resamples contiguous blocks of consecutive observations and",
        "recomputes each statistic.  The interval measures within-series sampling",
        "uncertainty.  It does not include parameter uncertainty, model uncertainty",
        "or variation across seeds.  That last source is measured in",
        "`docs/robustness.md`.",
        "",
        "The block length is 1000, well above the largest lag used here (50).",
        "Shorter blocks would attenuate the autocorrelation at long lags.",
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
