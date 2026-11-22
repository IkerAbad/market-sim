"""Run the baseline simulation and write the results table.

Examples
--------
python scripts/run_simulation.py --config configs/baseline.json --output results
python scripts/run_simulation.py --seed 7 --output results_seed7
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import (  # noqa: E402
    all_facts_pass,
    apply_overrides,
    compute_metrics,
    evaluate_facts,
    format_markdown_table,
    load_config,
    save_series_csv,
    simulate,
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
        "--output",
        type=Path,
        default=ROOT / "results",
        help="directory for series.csv, metrics.json, config.json and results.md",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="optional seed override, useful for sensitivity checks",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="override a dotted configuration key, for example model.price_impact=0.1",
    )
    return parser.parse_args()


def parse_overrides(items: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"override must have the form KEY=VALUE: {item!r}")
        key, value = item.split("=", 1)
        overrides[key.strip()] = value.strip()
    return overrides


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    if args.set:
        config = apply_overrides(config, parse_overrides(args.set))
    if args.seed is not None:
        config = replace(config, seed=args.seed)

    result = simulate(config)
    returns, volume = result.analysis_window()
    metrics = compute_metrics(returns, volume, config.metrics)
    facts = evaluate_facts(metrics, config.metrics)
    table = format_markdown_table(facts)
    passed = all_facts_pass(facts)

    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    save_series_csv(result, output / "series.csv")
    with (output / "config.json").open("w", encoding="utf-8") as handle:
        json.dump(asdict(config), handle, indent=2)
        handle.write("\n")

    summary = {
        "seed": config.seed,
        "n_steps": config.n_steps,
        "burn_in": config.burn_in,
        "n_observations": metrics["n_observations"],
        "metrics": metrics,
        "thresholds": asdict(config.metrics),
        "facts": facts,
        "all_facts_pass": passed,
    }
    with (output / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")

    report_lines = [
        "# Results",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/run_simulation.py --config {args.config.as_posix()} "
            f"--output {args.output.as_posix()}"
        ),
        "```",
        "",
        f"- Seed: {config.seed}",
        f"- Simulated steps: {config.n_steps}",
        f"- Burn-in: {config.burn_in}",
        f"- Observations in the table: {metrics['n_observations']}",
        f"- All criteria pass: {'yes' if passed else 'no'}",
        "",
        table,
        "",
    ]
    (output / "results.md").write_text("\n".join(report_lines), encoding="utf-8")

    print(table)
    print()
    print(f"series:  {output / 'series.csv'}")
    print(f"metrics: {output / 'metrics.json'}")
    print(f"report:  {output / 'results.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
