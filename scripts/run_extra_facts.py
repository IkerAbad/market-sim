"""Measure additional stylized facts and report the failures honestly.

Examples
--------
python scripts/run_extra_facts.py --results results --report docs/additional_facts.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_series_csv  # noqa: E402
from market_sim.extra_facts import (  # noqa: E402
    additional_metrics,
    evaluate_additional_facts,
    format_additional_table,
    format_aggregational_table,
    write_additional_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        default=ROOT / "results",
        help="directory containing series.csv",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "additional_facts.md",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "docs" / "additional_facts.csv",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    args = parse_args()
    data = load_series_csv(args.results / "series.csv")
    metrics = additional_metrics(data["return"], data["volume"])
    rows = evaluate_additional_facts(metrics)
    table = format_additional_table(rows)
    aggregation_table = format_aggregational_table(metrics)
    write_additional_csv(rows, args.csv)

    pass_count = sum(bool(row["passes"]) for row in rows)
    lines = [
        "# Additional stylized facts",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/run_extra_facts.py --results {display_path(args.results)} "
            f"--report {display_path(args.report)} --csv {display_path(args.csv)}"
        ),
        "```",
        "",
        f"- Observations: {len(data['return'])}",
        f"- Additional facts passing: {pass_count}/{len(rows)}",
        "",
        table,
        "",
        "## Kurtosis by horizon",
        "",
        "Returns are summed over disjoint blocks of the given length.  A model",
        "with aggregational Gaussianity shows a kurtosis that falls towards three",
        "as the horizon grows.",
        "",
        aggregation_table,
        "",
        "## Reading",
        "",
        "These diagnostics are not part of the original five facts.  They are",
        "reported to show what the model does not reproduce.  A failure here is a",
        "limitation of the model, not a bug in the simulator.  The thresholds are",
        "explicit choices, like the thresholds in the main table.",
        "",
        "The leverage effect is the correlation between a return and the next",
        "absolute return.  A negative value is the usual sign.  Gain/loss",
        "asymmetry compares the volatility of negative and positive returns.",
        "The DFA exponent measures long-range persistence in absolute returns.",
        "The volume lead-lag diagnostic finds the lag that maximises",
        "`corr(volume[t], abs(return[t + lag]))`.  Aggregational Gaussianity",
        "compares the kurtosis of 60-step returns with the kurtosis of one-step",
        "returns.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")

    print(table)
    print()
    print(f"passing: {pass_count}/{len(rows)}")
    print(f"report:  {args.report}")
    print(f"csv:     {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
