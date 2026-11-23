"""Verify that an installed market-sim reproduces the published baseline.

Run this from a directory outside the repository after installing the wheel or
the PyPI package.  The baseline configuration is packaged with the
distribution, so no repository file is needed.
"""

from __future__ import annotations

import math
import sys

from market_sim import compute_metrics, evaluate_facts, load_default_config, simulate

EXPECTED = {
    "kurtosis": 5.488,
    "acf_return_lag1": -0.004945,
    "acf_abs_return_lag1": 0.1443,
    "acf_abs_return_lag50": 0.1176,
    "corr_volume_abs_return": 0.5016,
    "tail_exceedance_ratio": 32.21,
}


def main() -> int:
    config = load_default_config()
    result = simulate(config)
    metrics = compute_metrics(*result.analysis_window(), config.metrics)
    for key, expected in EXPECTED.items():
        actual = float(metrics[key])
        if not math.isclose(actual, expected, rel_tol=1e-3, abs_tol=1e-6):
            print(f"{key}: {actual} != {expected}", file=sys.stderr)
            return 1
    facts = evaluate_facts(metrics, config.metrics)
    if not all(row["passes"] for row in facts):
        print(f"failing facts: {facts}", file=sys.stderr)
        return 1
    print("installed package reproduces the published baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
