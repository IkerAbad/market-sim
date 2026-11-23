"""Agent-based toy market simulator for stylized facts."""

from .ablations import (
    ABLATIONS,
    Ablation,
    AblationResult,
    AblationSummary,
    run_ablation_grid,
    summarize_ablations,
)
from .agents import CHARTIST, FUNDAMENTALIST, NOISE, Population
from .benchmark import BenchmarkResult, time_simulation
from .benchmarks import (
    BenchmarkPoint,
    benchmark_metrics,
    evaluate_benchmark,
    garch11_returns,
    gaussian_returns,
    student_t_returns,
)
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
from .docs import check_docs
from .ensemble import (
    EnsembleSummary,
    SeedResult,
    format_summary_markdown,
    parse_seeds,
    run_ensemble,
    run_seed,
    summarize_ensemble,
    wilson_interval,
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
from .price_volume import price_diagnostics, run_diagnostics, volume_diagnostics
from .real_data import compare_metrics, load_returns_csv
from .release import extract_release_notes
from .sample_size import (
    SampleSizePoint,
    SampleSizeSummary,
    run_sample_size_grid,
    summarize_sample_size,
)
from .sensitivity import (
    SENSITIVITY_VARIANTS,
    run_sensitivity_grid,
    summarize_sensitivity,
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
from .thresholds import (
    ThresholdRow,
    evaluate_thresholds,
    load_metrics_csv,
)

__version__ = "0.4.1"

__all__ = [
    "ABLATIONS",
    "CHARTIST",
    "FUNDAMENTALIST",
    "NOISE",
    "SENSITIVITY_VARIANTS",
    "Ablation",
    "AblationResult",
    "AblationSummary",
    "BenchmarkPoint",
    "BenchmarkResult",
    "BootstrapResult",
    "BootstrapSummary",
    "EnsembleSummary",
    "MetricsParams",
    "ModelParams",
    "PhasePoint",
    "PhaseSummary",
    "Population",
    "SampleSizePoint",
    "SampleSizeSummary",
    "SeedResult",
    "SimulationConfig",
    "SimulationResult",
    "ThresholdRow",
    "additional_metrics",
    "all_facts_pass",
    "apply_overrides",
    "autocorrelation",
    "benchmark_metrics",
    "block_indices",
    "bootstrap_metrics",
    "check_docs",
    "compare_metrics",
    "compute_metrics",
    "config_from_dict",
    "config_to_dict",
    "correlation",
    "dfa_hurst",
    "evaluate_benchmark",
    "evaluate_facts",
    "evaluate_thresholds",
    "extract_release_notes",
    "format_markdown_table",
    "format_summary_markdown",
    "gain_loss_asymmetry",
    "garch11_returns",
    "gaussian_returns",
    "kurtosis",
    "leverage_effect",
    "load_config",
    "load_metrics_csv",
    "load_returns_csv",
    "load_series_csv",
    "parse_seeds",
    "plot_phase_heatmap",
    "price_diagnostics",
    "run_ablation_grid",
    "run_diagnostics",
    "run_ensemble",
    "run_phase_grid",
    "run_sample_size_grid",
    "run_seed",
    "run_sensitivity_grid",
    "save_series_csv",
    "simulate",
    "student_t_returns",
    "summarize_ablations",
    "summarize_ensemble",
    "summarize_phase",
    "summarize_sample_size",
    "summarize_sensitivity",
    "tail_exceedance_ratio",
    "time_simulation",
    "volume_diagnostics",
    "volume_volatility_lead_lag",
    "wilson_interval",
    "write_ensemble_csv",
]
