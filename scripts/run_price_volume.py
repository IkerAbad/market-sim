"""Describe the price gap and the volume series.

Examples
--------
python scripts/run_price_volume.py --results results --report docs/price_volume.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config, load_series_csv  # noqa: E402
from market_sim.price_volume import (  # noqa: E402
    format_diagnostics_markdown,
    run_diagnostics,
    write_diagnostics_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline.json",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=ROOT / "results",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "price_volume.md",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "docs" / "price_volume.csv",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    data = load_series_csv(args.results / "series.csv")
    metrics = run_diagnostics(
        data["log_price"],
        data["return"],
        data["volume"],
        config.model.fundamental_value,
    )
    write_diagnostics_csv(metrics, args.csv)

    table = format_diagnostics_markdown(metrics)
    lines = [
        "# Price and volume diagnostics",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/run_price_volume.py --config {args.config.as_posix()} "
            f"--results {args.results.as_posix()}"
        ),
        "```",
        "",
        f"- Observations: {len(data['return'])}",
        f"- Fundamental value: {config.model.fundamental_value:g}",
        "",
        table,
        "",
        "## Reading",
        "",
        "These are descriptive diagnostics, not target facts.  The price gap is",
        "stationary around the constant fundamental value.  Its AR(1) coefficient",
        "and half-life describe how quickly the fundamentalists pull the price",
        "back.  The volume is heavy-tailed and autocorrelated.  Its correlation",
        "with absolute returns is the quantity used in fact 4.",
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
