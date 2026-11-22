"""Figures used in the README and in ``docs/``."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .stylized import autocorrelation

_BLUE = "#1f4e79"
_RED = "#c0504d"
_GREY = "#666666"

_STYLE = {
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 120,
    "savefig.dpi": 150,
}


def _prepare_output(path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def plot_price_series(
    prices: np.ndarray,
    path: str | Path,
    fundamental_value: float | None = None,
    start_step: int = 0,
) -> Path:
    """Plot a price level series."""
    values = np.asarray(prices, dtype=float)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("prices must be a one-dimensional series")
    if not np.all(np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("prices must be finite and positive")
    output = _prepare_output(path)
    steps = np.arange(start_step, start_step + values.size)

    with plt.rc_context(_STYLE):
        figure, axis = plt.subplots(figsize=(10, 4))
        axis.plot(steps, values, color=_BLUE, linewidth=0.9)
        if fundamental_value is not None:
            axis.axhline(
                fundamental_value,
                color=_GREY,
                linewidth=0.9,
                linestyle="--",
                label="Fundamental value",
            )
            axis.legend(frameon=False)
        axis.set_xlabel("Step")
        axis.set_ylabel("Price")
        axis.set_title("Simulated price series")
        figure.savefig(output, bbox_inches="tight")
        plt.close(figure)
    return output


def plot_return_histogram(
    returns: np.ndarray,
    path: str | Path,
    tail_sigma: float = 6.0,
    bins: int = 150,
) -> Path:
    """Histogram of returns with a normal density overlay on a log y-axis."""
    values = np.asarray(returns, dtype=float)
    if values.ndim != 1 or values.size < 10:
        raise ValueError("returns must be a one-dimensional series")
    if not np.all(np.isfinite(values)):
        raise ValueError("returns contain non-finite values")
    centred = values - values.mean()
    standard_deviation = float(centred.std())
    if standard_deviation == 0.0:
        raise ValueError("cannot plot a histogram of a constant series")
    if tail_sigma <= 0:
        raise ValueError("tail_sigma must be positive")
    if bins < 10:
        raise ValueError("bins must be at least 10")

    limit = tail_sigma * standard_deviation
    grid = np.linspace(-limit, limit, 500)
    normal_density = np.exp(-0.5 * (grid / standard_deviation) ** 2) / (
        standard_deviation * np.sqrt(2.0 * np.pi)
    )

    output = _prepare_output(path)
    with plt.rc_context(_STYLE):
        figure, axis = plt.subplots(figsize=(7, 4.5))
        axis.hist(
            centred,
            bins=bins,
            range=(-limit, limit),
            density=True,
            color=_BLUE,
            alpha=0.65,
            label="Simulated returns",
        )
        axis.plot(grid, normal_density, color=_RED, linewidth=1.4, label="Normal")
        axis.set_yscale("log")
        axis.set_xlabel("Return")
        axis.set_ylabel("Density (log scale)")
        axis.set_title("Return distribution")
        axis.legend(frameon=False)
        figure.savefig(output, bbox_inches="tight")
        plt.close(figure)
    return output


def plot_autocorrelation(
    returns: np.ndarray,
    path: str | Path,
    max_lag: int = 100,
) -> Path:
    """Autocorrelation of returns and of absolute returns."""
    values = np.asarray(returns, dtype=float)
    if values.ndim != 1 or values.size < 10:
        raise ValueError("returns must be a one-dimensional series")
    if max_lag < 1 or max_lag >= values.size:
        raise ValueError("max_lag must be positive and smaller than the sample")
    centred = values - values.mean()
    acf_returns = autocorrelation(values, max_lag)
    acf_absolute = autocorrelation(np.abs(centred), max_lag)
    lags = np.arange(1, max_lag + 1)
    confidence = 1.96 / np.sqrt(values.size)

    output = _prepare_output(path)
    with plt.rc_context(_STYLE):
        figure, axis = plt.subplots(figsize=(10, 4))
        axis.axhspan(
            -confidence,
            confidence,
            color=_GREY,
            alpha=0.15,
            label="95% white-noise band",
        )
        axis.axhline(0.0, color="black", linewidth=0.8)
        axis.plot(
            lags,
            acf_returns[1:],
            color=_BLUE,
            linewidth=1.0,
            marker="o",
            markersize=2,
            label="Returns",
        )
        axis.plot(
            lags,
            acf_absolute[1:],
            color=_RED,
            linewidth=1.2,
            marker="o",
            markersize=2,
            label="Absolute returns",
        )
        axis.set_xlim(1, max_lag)
        axis.set_xlabel("Lag")
        axis.set_ylabel("Autocorrelation")
        axis.set_title("Autocorrelation of returns and absolute returns (lag 0 omitted)")
        axis.legend(frameon=False, ncols=3)
        figure.savefig(output, bbox_inches="tight")
        plt.close(figure)
    return output
