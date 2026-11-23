"""Discrimination on the additional facts that do not need volume.

Examples
--------
python scripts/run_additional_discrimination.py --seeds 1001-1020 --series 100
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim import load_config  # noqa: E402
from market_sim.additional_discrimination import (  # noqa: E402
    additional_discrimination_rows,
    format_additional_discrimination_markdown,
    run_model_ensemble,
    samples_from_generator,
    write_additional_discrimination_csv,
)
from market_sim.benchmarks import garch11_returns, gaussian_returns  # noqa: E402
from market_sim.ensemble import parse_seeds  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "baseline.json")
    parser.add_argument("--seeds", default="1001-1020")
    parser.add_argument("--series", type=int, default=100)
    parser.add_argument("--n", type=int, default=100000)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "additional_discrimination.md",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "docs" / "additional_discrimination.csv",
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
    seeds = parse_seeds(args.seeds)
    model = run_model_ensemble(config, seeds, jobs=args.jobs)
    garch = samples_from_generator(
        lambda n, seed: garch11_returns(n, seed=seed),
        args.series,
        args.n,
        base_seed=3000,
    )
    gaussian = samples_from_generator(
        lambda n, seed: gaussian_returns(n, seed=seed),
        args.series,
        args.n,
        base_seed=1000,
    )
    rows = additional_discrimination_rows(model, garch, gaussian)
    write_additional_discrimination_csv(rows, args.csv)

    by_key = {row.key: row for row in rows}
    dfa = by_key["dfa_hurst_abs"]
    leverage = by_key["leverage_lag1"]
    asymmetry = by_key["gain_loss_volatility_ratio"]
    aggregation = by_key["aggregational_ratio"]
    table = format_additional_discrimination_markdown(rows)
    paragraph = textwrap.fill(
        f"DFA Hurst separates the model from GARCH with AUC {dfa.auc_garch:.3f}. "
        f"Aggregational Gaussianity separates them moderately, with AUC "
        f"{aggregation.auc_garch:.3f}, because the model ratio is "
        f"{aggregation.model_median:.3f} and the GARCH ratio is "
        f"{aggregation.garch_median:.3f}. Leverage does not separate them in the "
        f"intended direction: AUC {leverage.auc_garch:.3f}, and the model median "
        f"is {leverage.model_median:.4g} against {leverage.garch_median:.4g} for "
        f"GARCH. Gain/loss asymmetry is close to a coin flip, with AUC "
        f"{asymmetry.auc_garch:.3f} and both medians near 1. The additional facts "
        "add the DFA exponent and aggregational Gaussianity to the "
        "discriminators. Leverage and gain/loss do not help. The DFA exponent "
        "and ACF(abs, 50) are two views of the same slow persistence, so the "
        "model's distinctive content is long memory.",
        width=88,
    )
    lines = [
        "# Additional facts against the benchmarks",
        "",
        "Command:",
        "",
        "```",
        (
            f"python scripts/run_additional_discrimination.py "
            f"--config {display_path(args.config)} --seeds {args.seeds} "
            f"--series {args.series} --n {args.n} --jobs {args.jobs}"
        ),
        "```",
        "",
        f"- Model sample: {len(model)} seeds",
        f"- GARCH and Gaussian samples: {args.series} series each",
        f"- Observations per series: {args.n}",
        "- The volume lead-lag fact is omitted because the synthetic benchmarks",
        "  have no volume.",
        "",
        table,
        "",
        "## Reading",
        "",
        paragraph,
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
