"""Discriminative power of the price facts against GARCH and Gaussian noise.

Examples
--------
python scripts/run_discrimination.py --series 100 --n 100000
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config  # noqa: E402
from market_sim.benchmark_rates import metrics_from_generator  # noqa: E402
from market_sim.benchmarks import garch11_returns, gaussian_returns  # noqa: E402
from market_sim.discrimination import (  # noqa: E402
    discrimination_rows,
    format_discrimination_markdown,
    format_grid_markdown,
    plot_threshold_grid,
    threshold_grid,
    write_discrimination_csv,
    write_grid_csv,
)
from market_sim.strict import load_seed_metrics  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "baseline.json")
    parser.add_argument("--model-csv", type=Path, default=ROOT / "docs" / "robustness_50.csv")
    parser.add_argument("--series", type=int, default=100)
    parser.add_argument("--n", type=int, default=100000)
    parser.add_argument("--report", type=Path, default=ROOT / "docs" / "discrimination.md")
    parser.add_argument("--csv", type=Path, default=ROOT / "docs" / "discrimination.csv")
    parser.add_argument(
        "--grid-csv",
        type=Path,
        default=ROOT / "docs" / "discrimination_grid.csv",
    )
    parser.add_argument(
        "--figure",
        type=Path,
        default=ROOT / "docs" / "discrimination.png",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    params = config.metrics
    model = load_seed_metrics(args.model_csv)
    garch = metrics_from_generator(
        lambda n, seed: garch11_returns(n, seed=seed),
        params,
        args.series,
        args.n,
        base_seed=3000,
    )
    gaussian = metrics_from_generator(
        lambda n, seed: gaussian_returns(n, seed=seed),
        params,
        args.series,
        args.n,
        base_seed=1000,
    )
    rows = discrimination_rows(model, garch, gaussian)
    cells = threshold_grid(model, garch, gaussian, params)
    write_discrimination_csv(rows, args.csv)
    write_grid_csv(cells, args.grid_csv)

    kurtosis_thresholds = (3.0, 4.0, 5.0, 6.0, 8.0, 10.0)
    tail_thresholds = (1.0, 2.0, 5.0, 10.0, 20.0, 50.0)
    plot_threshold_grid(
        cells,
        kurtosis_thresholds,
        tail_thresholds,
        args.figure,
    )

    strict_cell = next(cell for cell in cells if cell.kurtosis == 5.0 and cell.tail == 10.0)
    loose_cell = next(cell for cell in cells if cell.kurtosis == 4.0 and cell.tail == 10.0)
    kurtosis_row = next(row for row in rows if row.key == "kurtosis")
    abs50_row = next(row for row in rows if row.key == "acf_abs_return_lag50")
    abs1_row = next(row for row in rows if row.key == "acf_abs_return_lag1")

    table = format_discrimination_markdown(rows)
    grid_table = format_grid_markdown(cells)
    grid_paragraph = textwrap.fill(
        f"At kurtosis > 5 and tail ratio > 10 the model passes all five in "
        f"{strict_cell.model_pass}/{strict_cell.model_total} seeds, GARCH in "
        f"{strict_cell.garch_pass}/{strict_cell.garch_total} and Gaussian in "
        f"{strict_cell.gaussian_pass}/{strict_cell.gaussian_total}.  At kurtosis "
        f"> 4 the model passes {loose_cell.model_pass}/{loose_cell.model_total} "
        f"and GARCH {loose_cell.garch_pass}/{loose_cell.garch_total}.  The "
        "separation is sharpest between 4 and 5, where GARCH loses almost all "
        "of its passes while the model keeps most of them.  The grid is a "
        "sensitivity map, not a licence to choose the best cell after seeing "
        "the data.  The strict thresholds were fixed from the benchmark pass "
        "rates before this grid was computed.",
        width=88,
    )
    lines = [
        "# Discrimination between the model and the benchmarks",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/run_discrimination.py --config {display_path(args.config)} "
            f"--series {args.series} --n {args.n}"
        ),
        "```",
        "",
        f"- Model sample: {len(model)} seeds from `{display_path(args.model_csv)}`",
        f"- GARCH and Gaussian samples: {args.series} series each",
        f"- Observations per synthetic series: {args.n}",
        "- AUC is the probability that a random model value is on the model side",
        "  of a random benchmark value.  0.5 means no separation.  The brackets",
        "  are 95% bootstrap percentile intervals.",
        "",
        "## Area under the ROC curve",
        "",
        table,
        "",
        "## Threshold grid",
        "",
        "The table reports the all-five pass rate over kurtosis and tail-ratio",
        "thresholds.  The other three criteria are fixed.  The figure",
        f"`{display_path(args.figure)}` shows the same grid as heatmaps.",
        "",
        grid_table,
        "",
        "## Reading",
        "",
        f"Kurtosis separates the model from GARCH with AUC {kurtosis_row.auc_garch:.3f}.",
        f"ACF(abs, 50) separates them with AUC {abs50_row.auc_garch:.3f}.",
        f"ACF(abs, 1) is close to a coin flip, with AUC {abs1_row.auc_garch:.3f}.",
        "The two clustering facts are not equally informative: the slow",
        "autocorrelation is the stronger discriminator.",
        "",
        grid_paragraph,
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")

    print(table)
    print()
    print(grid_table)
    print()
    print(f"report: {args.report}")
    print(f"csv:    {args.csv}")
    print(f"grid:   {args.grid_csv}")
    print(f"figure: {args.figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
