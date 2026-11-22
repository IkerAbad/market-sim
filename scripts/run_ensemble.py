"""Run the baseline configuration over a set of seeds and summarize it.

Examples
--------
python scripts/run_ensemble.py --config configs/baseline.json --seeds 1001-1020 --jobs 8
python scripts/run_ensemble.py --seeds 1-5,10 --output results_small --report docs/small.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config  # noqa: E402
from market_sim.ensemble import (  # noqa: E402
    format_summary_markdown,
    parse_seeds,
    run_ensemble,
    summarize_ensemble,
    summary_to_dict,
    write_ensemble_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline.json",
        help="JSON configuration file",
    )
    parser.add_argument(
        "--seeds",
        default="1001-1020",
        help="seed list or ranges, for example 1-20 or 1,2,5-7",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=0,
        help="worker processes, 0 means min(8, CPU count)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results_ensemble",
        help="directory for metrics.csv, summary.json and robustness.md",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "robustness.md",
        help="Markdown report path",
    )
    parser.add_argument(
        "--csv-report",
        type=Path,
        default=ROOT / "docs" / "robustness.csv",
        help="per-seed CSV path committed with the report",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    seeds = parse_seeds(args.seeds)
    jobs = args.jobs if args.jobs > 0 else min(8, os.cpu_count() or 1)
    print(f"running {len(seeds)} seeds with {jobs} worker(s)")

    results = run_ensemble(config, seeds, jobs=jobs)
    summary = summarize_ensemble(results)
    table = format_summary_markdown(summary)

    args.output.mkdir(parents=True, exist_ok=True)
    write_ensemble_csv(results, args.output / "metrics.csv")
    write_ensemble_csv(results, args.csv_report)
    summary_payload = {
        "config": asdict(config),
        "seeds": seeds,
        "n_steps": config.n_steps,
        "burn_in": config.burn_in,
        "command": (
            f"python scripts/run_ensemble.py --config {args.config.as_posix()} "
            f"--seeds {args.seeds} --jobs {jobs}"
        ),
        **summary_to_dict(summary),
    }
    with (args.output / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary_payload, handle, indent=2)
        handle.write("\n")

    overall = f"{summary.overall_pass_count}/{summary.n_seeds}"
    try:
        csv_display = args.csv_report.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        csv_display = args.csv_report.as_posix()
    lines = [
        "# Robustness across seeds",
        "",
        "Command:",
        "",
        "```",
        summary_payload["command"],
        "```",
        "",
        f"- Configuration: `{args.config.as_posix()}`",
        f"- Seeds: {seeds[0]} to {seeds[-1]} ({len(seeds)} seeds)",
        f"- Steps per seed: {config.n_steps}, burn-in: {config.burn_in}",
        f"- Seeds passing all six statistic rows: {overall}",
        f"- Per-seed values: `{csv_display}`",
        "",
        table,
        "",
        "## Reading",
        "",
        "The baseline seed 20261122 is not in this set.  The seeds above were not",
        "used to choose the parameters, so this table is a seed hold-out.  It",
        "measures sampling variation, not variation in the model specification.",
        "The pass counts use the same thresholds as the single-run table.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")

    print(table)
    print()
    print(f"seeds passing all rows: {overall}")
    print(f"metrics: {args.output / 'metrics.csv'}")
    print(f"report:  {args.report}")
    print(f"csv:     {args.csv_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
