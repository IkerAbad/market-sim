"""Build the three figures from a saved run, or run the simulation if needed.

Examples
--------
python scripts/make_figures.py --results results --output docs
python scripts/make_figures.py --config configs/baseline.json --output docs
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")

from market_sim import load_config, load_series_csv, simulate  # noqa: E402
from market_sim.plots import (  # noqa: E402
    plot_autocorrelation,
    plot_price_series,
    plot_return_histogram,
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
        "--results",
        type=Path,
        default=ROOT / "results",
        help="directory containing series.csv (optional)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs",
        help="directory for the PNG files",
    )
    parser.add_argument(
        "--max-lag",
        type=int,
        default=100,
        help="maximum lag in the autocorrelation figure",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    series_path = args.results / "series.csv"

    if series_path.exists():
        data = load_series_csv(series_path)
        prices = data["price"]
        returns = data["return"]
        start_step = int(data["step"][0])
        source = series_path
    else:
        result = simulate(config)
        prices = [math.exp(value) for value in result.price_window()]
        returns = result.analysis_window()[0]
        start_step = config.burn_in
        source = None

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

    if source is None:
        print("series.csv not found, simulated the configuration in memory")
    else:
        print(f"read {source}")
    print(f"price series:  {price_path}")
    print(f"histogram:     {histogram_path}")
    print(f"autocorrelation: {acf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
