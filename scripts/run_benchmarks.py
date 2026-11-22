"""Compare the model with simple synthetic return processes.

Examples
--------
python scripts/run_benchmarks.py --config configs/baseline.json
    --results results --report docs/benchmarks.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config, load_series_csv  # noqa: E402
from market_sim.benchmarks import (  # noqa: E402
    benchmark_metrics,
    evaluate_benchmark,
    format_benchmark_markdown,
    garch11_returns,
    gaussian_returns,
    student_t_returns,
    write_benchmark_csv,
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
        help="directory containing the model series.csv",
    )
    parser.add_argument("--n", type=int, default=100000)
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "benchmarks.md",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "docs" / "benchmarks.csv",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    model_data = load_series_csv(args.results / "series.csv")
    params = config.metrics
    n = args.n

    model_metrics = benchmark_metrics(model_data["return"], params)
    points = [
        evaluate_benchmark(
            "market-sim baseline",
            "Agent-based model, volume fact omitted here",
            model_metrics,
            params,
        ),
        evaluate_benchmark(
            "Gaussian",
            "Independent normal returns",
            benchmark_metrics(gaussian_returns(n, seed=1), params),
            params,
        ),
        evaluate_benchmark(
            "Student-t(5)",
            "Independent Student-t returns",
            benchmark_metrics(student_t_returns(n, df=5.0, seed=2), params),
            params,
        ),
        evaluate_benchmark(
            "GARCH(1,1)",
            "Gaussian GARCH with alpha 0.08 and beta 0.90",
            benchmark_metrics(garch11_returns(n, seed=3), params),
            params,
        ),
    ]
    table = format_benchmark_markdown(points)
    write_benchmark_csv(points, args.csv)

    lines = [
        "# Synthetic benchmarks",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/run_benchmarks.py --config {args.config.as_posix()} "
            f"--results {args.results.as_posix()} --n {n}"
        ),
        "```",
        "",
        f"- Observations per series: {n}",
        "- The table uses the five price facts.  The volume fact is omitted",
        "  because the benchmarks have no volume.",
        "- The model row uses the same 100,000 returns as the main table.",
        "",
        table,
        "",
        "## Reading",
        "",
        "Gaussian returns fail the fat-tail and clustering facts.  Student-t",
        "returns have fat tails but no volatility clustering.  GARCH(1,1) passes",
        "the five price facts in this sample.  The five facts alone therefore do",
        "not distinguish the agent-based model from a simple stochastic-volatility",
        "benchmark.  The model's additional content is the endogenous volume and",
        "the explicit agent rules.  The volume fact is not in this table because",
        "the benchmarks have no volume.",
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
