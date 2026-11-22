"""Command-line interface for the core workflow.

The analysis scripts for bootstrap intervals, phase maps and additional facts
remain standalone.  This module covers the three commands used in the main
README workflow: ``simulate``, ``figures`` and ``ensemble``.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from . import __version__
from .config import apply_overrides, load_config
from .ensemble import (
    format_summary_markdown,
    parse_seeds,
    run_ensemble,
    summarize_ensemble,
    summary_to_dict,
    wilson_interval,
    write_ensemble_csv,
)
from .market import load_series_csv, save_series_csv, simulate
from .stylized import (
    all_facts_pass,
    compute_metrics,
    evaluate_facts,
    format_markdown_table,
)


def _parse_overrides(items: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"override must have the form KEY=VALUE: {item!r}")
        key, value = item.split("=", 1)
        overrides[key.strip()] = value.strip()
    return overrides


def add_simulate_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/baseline.json"),
        help="JSON configuration file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results"),
        help="directory for series.csv, metrics.json, config.json and results.md",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="optional seed override",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="override a dotted configuration key",
    )


def run_simulate(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if args.set:
        config = apply_overrides(config, _parse_overrides(args.set))
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


def simulate_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the baseline simulation.")
    add_simulate_arguments(parser)
    args = parser.parse_args(argv)
    try:
        return run_simulate(args)
    except (KeyError, ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))


def add_figures_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/baseline.json"),
        help="JSON configuration file",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("results"),
        help="directory containing series.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs"),
        help="directory for the PNG files",
    )
    parser.add_argument(
        "--max-lag",
        type=int,
        default=100,
        help="maximum lag in the autocorrelation figure",
    )


def run_figures(args: argparse.Namespace) -> int:
    import matplotlib

    matplotlib.use("Agg")
    from .plots import plot_autocorrelation, plot_price_series, plot_return_histogram

    config = load_config(args.config)
    series_path = args.results / "series.csv"
    if series_path.exists():
        data = load_series_csv(series_path)
        prices = data["price"]
        returns = data["return"]
        start_step = int(data["step"][0])
    else:
        result = simulate(config)
        prices = np.exp(result.price_window())
        returns = result.analysis_window()[0]
        start_step = config.burn_in

    args.output.mkdir(parents=True, exist_ok=True)
    price_path = plot_price_series(
        prices,
        args.output / "price_series.png",
        fundamental_value=config.model.fundamental_value,
        start_step=start_step,
    )
    histogram_path = plot_return_histogram(
        returns,
        args.output / "return_histogram.png",
    )
    max_lag = min(args.max_lag, len(returns) - 1)
    acf_path = plot_autocorrelation(
        returns,
        args.output / "autocorrelation.png",
        max_lag=max_lag,
    )
    print(f"price series:  {price_path}")
    print(f"histogram:     {histogram_path}")
    print(f"autocorrelation: {acf_path}")
    return 0


def figures_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the three figures.")
    add_figures_arguments(parser)
    args = parser.parse_args(argv)
    try:
        return run_figures(args)
    except (KeyError, ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))


def add_ensemble_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/baseline.json"),
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
        default=Path("results_ensemble"),
        help="directory for metrics.csv and summary.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/robustness.md"),
        help="Markdown report path",
    )
    parser.add_argument(
        "--csv-report",
        type=Path,
        default=Path("docs/robustness.csv"),
        help="per-seed CSV path",
    )


def run_ensemble_command(args: argparse.Namespace) -> int:
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
    payload = {
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
    lower, upper = wilson_interval(summary.overall_pass_count, summary.n_seeds)
    payload["all_pass_interval"] = [lower, upper]
    with (args.output / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    overall = f"{summary.overall_pass_count}/{summary.n_seeds}"
    lines = [
        "# Robustness across seeds",
        "",
        "Command:",
        "",
        "```",
        payload["command"],
        "```",
        "",
        f"- Configuration: `{args.config.as_posix()}`",
        f"- Seeds: {seeds[0]} to {seeds[-1]} ({len(seeds)} seeds)",
        f"- Steps per seed: {config.n_steps}, burn-in: {config.burn_in}",
        f"- Seeds passing all six statistic rows: {overall}",
        f"- 95% Wilson interval for the all-pass rate: [{lower:.3f}, {upper:.3f}]",
        f"- Per-seed values: `{args.csv_report.as_posix()}`",
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


def ensemble_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a multi-seed ensemble.")
    add_ensemble_arguments(parser)
    args = parser.parse_args(argv)
    try:
        return run_ensemble_command(args)
    except (KeyError, ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))


def _run_version(args: argparse.Namespace) -> int:
    print(__version__)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="market-sim",
        description="Agent-based toy market simulator for stylized facts.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate_parser = subparsers.add_parser("simulate", help="run the baseline simulation")
    add_simulate_arguments(simulate_parser)
    figures_parser = subparsers.add_parser("figures", help="build the three figures")
    add_figures_arguments(figures_parser)
    ensemble_parser = subparsers.add_parser("ensemble", help="run a multi-seed ensemble")
    add_ensemble_arguments(ensemble_parser)
    subparsers.add_parser("version", help="print the package version")

    handlers = {
        "simulate": run_simulate,
        "figures": run_figures,
        "ensemble": run_ensemble_command,
        "version": _run_version,
    }
    args = parser.parse_args(argv)
    try:
        return handlers[args.command](args)
    except (KeyError, ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
