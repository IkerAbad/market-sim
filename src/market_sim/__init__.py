"""Agent-based toy market simulator for stylized facts."""

from .agents import CHARTIST, FUNDAMENTALIST, NOISE, Population
from .config import (
    MetricsParams,
    ModelParams,
    SimulationConfig,
    apply_overrides,
    config_from_dict,
    config_to_dict,
    load_config,
)
from .market import SimulationResult, load_series_csv, save_series_csv, simulate
from .stylized import (
    all_facts_pass,
    autocorrelation,
    compute_metrics,
    evaluate_facts,
    format_markdown_table,
    kurtosis,
    tail_exceedance_ratio,
)

__version__ = "0.1.0"

__all__ = [
    "CHARTIST",
    "FUNDAMENTALIST",
    "NOISE",
    "MetricsParams",
    "ModelParams",
    "Population",
    "SimulationConfig",
    "SimulationResult",
    "all_facts_pass",
    "apply_overrides",
    "autocorrelation",
    "compute_metrics",
    "config_from_dict",
    "config_to_dict",
    "evaluate_facts",
    "format_markdown_table",
    "kurtosis",
    "load_config",
    "load_series_csv",
    "save_series_csv",
    "simulate",
    "tail_exceedance_ratio",
]
