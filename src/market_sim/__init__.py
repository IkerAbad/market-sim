"""Agent-based toy market simulator for stylized facts."""

from .agents import CHARTIST, FUNDAMENTALIST, NOISE, Population
from .bootstrap import (
    BootstrapResult,
    BootstrapSummary,
    block_indices,
    bootstrap_metrics,
)
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
from .extra_facts import (
    additional_metrics,
    dfa_hurst,
    gain_loss_asymmetry,
    leverage_effect,
    volume_volatility_lead_lag,
)
from .market import SimulationResult, load_series_csv, save_series_csv, simulate
from .phase import (
    PhasePoint,
    PhaseSummary,
    plot_phase_heatmap,
    run_phase_grid,
    summarize_phase,
)
from .stylized import (
    all_facts_pass,
    autocorrelation,
    compute_metrics,
    correlation,
    evaluate_facts,
    format_markdown_table,
    kurtosis,
    tail_exceedance_ratio,
)

__version__ = "0.2.0"

__all__ = [
    "CHARTIST",
    "FUNDAMENTALIST",
    "NOISE",
    "BootstrapResult",
    "BootstrapSummary",
    "EnsembleSummary",
    "MetricsParams",
    "ModelParams",
    "PhasePoint",
    "PhaseSummary",
    "Population",
    "SeedResult",
    "SimulationConfig",
    "SimulationResult",
    "additional_metrics",
    "all_facts_pass",
    "apply_overrides",
    "autocorrelation",
    "block_indices",
    "bootstrap_metrics",
    "compute_metrics",
    "config_from_dict",
    "config_to_dict",
    "correlation",
    "dfa_hurst",
    "evaluate_facts",
    "format_markdown_table",
    "format_summary_markdown",
    "gain_loss_asymmetry",
    "kurtosis",
    "leverage_effect",
    "load_config",
    "load_series_csv",
    "parse_seeds",
    "plot_phase_heatmap",
    "run_ensemble",
    "run_phase_grid",
    "run_seed",
    "save_series_csv",
    "simulate",
    "summarize_ensemble",
    "summarize_phase",
    "tail_exceedance_ratio",
    "volume_volatility_lead_lag",
    "write_ensemble_csv",
]
