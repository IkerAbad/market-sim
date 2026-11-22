"""One-at-a-time parameter sensitivity over the stylized facts."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .ablations import (
    Ablation,
    AblationResult,
    AblationSummary,
    format_ablation_markdown,
    run_ablation_grid,
    summarize_ablations,
)
from .config import SimulationConfig

SENSITIVITY_VARIANTS: tuple[Ablation, ...] = (
    Ablation("baseline", "No parameter change", {}),
    Ablation("activity_0.5", "Much lower activity volatility", {"activity_sigma": 0.5}),
    Ablation("activity_0.75", "Lower activity volatility", {"activity_sigma": 0.75}),
    Ablation("activity_1.25", "Higher activity volatility", {"activity_sigma": 1.25}),
    Ablation("activity_2.0", "Much higher activity volatility", {"activity_sigma": 2.0}),
    Ablation("chartist_0.05", "Weaker chartists", {"max_chartist_demand": 0.05}),
    Ablation("chartist_0.20", "Stronger chartists", {"max_chartist_demand": 0.20}),
    Ablation("chartist_0.50", "Much stronger chartists", {"max_chartist_demand": 0.50}),
    Ablation("chartist_1.00", "Extreme chartists", {"max_chartist_demand": 1.0}),
    Ablation("chartist_off", "Chartists submit zero demand", {"max_chartist_demand": 0.0}),
    Ablation("impact_0.025", "Lower price impact", {"price_impact": 0.025}),
    Ablation("impact_0.100", "Higher price impact", {"price_impact": 0.10}),
    Ablation("impact_0.200", "Much higher price impact", {"price_impact": 0.20}),
    Ablation("noise_0.5", "Lower noise demand", {"noise_demand_scale": 0.5}),
    Ablation("noise_2.0", "Higher noise demand", {"noise_demand_scale": 2.0}),
    Ablation("noise_5.0", "Much higher noise demand", {"noise_demand_scale": 5.0}),
    Ablation(
        "risk_low",
        "Lower risk aversion range",
        {"risk_aversion_min": 0.25, "risk_aversion_max": 1.0},
    ),
    Ablation(
        "risk_high",
        "Higher risk aversion range",
        {"risk_aversion_min": 1.0, "risk_aversion_max": 4.0},
    ),
    Ablation(
        "risk_very_low",
        "Very low risk aversion",
        {"risk_aversion_min": 0.1, "risk_aversion_max": 0.1},
    ),
    Ablation(
        "risk_very_high",
        "Very high risk aversion",
        {"risk_aversion_min": 10.0, "risk_aversion_max": 10.0},
    ),
    Ablation(
        "memory_very_short",
        "Very short memory range",
        {"memory_min": 1, "memory_max": 2},
    ),
    Ablation(
        "memory_short",
        "Shorter memory range",
        {"memory_min": 2, "memory_max": 100},
    ),
    Ablation(
        "memory_long",
        "Longer memory range",
        {"memory_min": 20, "memory_max": 5000},
    ),
    Ablation("bias_0.0", "No fundamentalist bias", {"fundamental_bias_std": 0.0}),
    Ablation("bias_0.1", "Larger fundamentalist bias", {"fundamental_bias_std": 0.1}),
    Ablation("bias_0.5", "Very large fundamentalist bias", {"fundamental_bias_std": 0.5}),
    Ablation(
        "wealth_equal",
        "Equal wealth weights",
        {"wealth_min": 1.0, "wealth_max": 1.0},
    ),
    Ablation(
        "fundamental_kappa_0.5",
        "Weaker fundamentalist response",
        {"kappa_fundamentalist": 0.5},
    ),
    Ablation(
        "fundamental_kappa_2.0",
        "Stronger fundamentalist response",
        {"kappa_fundamentalist": 2.0},
    ),
    Ablation(
        "fundamental_max_0.5",
        "Lower fundamentalist demand cap",
        {"max_fundamentalist_demand": 0.5},
    ),
    Ablation(
        "fundamental_max_2.0",
        "Higher fundamentalist demand cap",
        {"max_fundamentalist_demand": 2.0},
    ),
    Ablation(
        "fundamental_off",
        "Fundamentalists submit zero demand",
        {"max_fundamentalist_demand": 0.0},
    ),
)


def run_sensitivity_grid(
    config: SimulationConfig,
    seeds: Iterable[int],
    jobs: int = 1,
) -> list[AblationResult]:
    """Run every sensitivity variant over the given seeds."""
    return run_ablation_grid(config, SENSITIVITY_VARIANTS, seeds, jobs=jobs)


def summarize_sensitivity(results: Sequence[AblationResult]) -> AblationSummary:
    """Aggregate the sensitivity results."""
    return summarize_ablations(results, SENSITIVITY_VARIANTS)


def format_sensitivity_markdown(summary: AblationSummary) -> str:
    """Render the sensitivity table with a Variant column."""
    return format_ablation_markdown(summary, first_column="Variant")


def sensitivity_report(summary: AblationSummary, command: str) -> str:
    """Build the Markdown report for the one-at-a-time sensitivity."""
    full = [
        name
        for index, name in enumerate(summary.names)
        if summary.all_pass_count[index] == summary.n_seeds
    ]
    partial = [
        name
        for index, name in enumerate(summary.names)
        if summary.all_pass_count[index] < summary.n_seeds
    ]
    lines = [
        "# One-at-a-time sensitivity",
        "",
        "Command:",
        "",
        "```",
        command,
        "```",
        "",
        f"- Seeds per variant: {summary.n_seeds}",
        "- Each cell is the number of seeds where that statistic passes.",
        "- The baseline row is the reference.",
        f"- Variants with all seeds passing: {', '.join(full) if full else 'none'}.",
        f"- Variants with at least one failing seed: {', '.join(partial) if partial else 'none'}.",
        "",
        format_sensitivity_markdown(summary),
        "",
        "## Reading",
        "",
        "This is a one-at-a-time scan, not a full factorial design.  A variant",
        "with a lower mean pass count identifies a parameter that the facts",
        "depend on.  The baseline row uses the same seeds as the other rows.",
        "",
    ]
    return "\n".join(lines)
