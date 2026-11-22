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
from .ensemble import (
    EnsembleSummary,
    SeedResult,
    format_summary_markdown,
    parse_seeds,
    run_ensemble,
    run_seed,
    summarize_ensemble,
    write_ensemble_csv,
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
    "EnsembleSummary",
    "MetricsParams",
    "ModelParams",
    "Population",
    "SeedResult",
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
    "format_summary_markdown",
    "kurtosis",
    "load_config",
    "load_series_csv",
    "parse_seeds",
    "run_ensemble",
    "run_seed",
    "save_series_csv",
    "simulate",
    "summarize_ensemble",
    "tail_exceedance_ratio",
    "write_ensemble_csv",
]
