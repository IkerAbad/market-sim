# Changelog

All notable changes to this project are documented in this file.

The format follows Keep a Changelog and the project uses semantic versioning.

## [Unreleased]

## [1.0.0] - 2026-11-23

### Added

- Paper `docs/paper.md`, a reproducible account of the model, the facts, the
  ablations and the negative result on the three agent types.
- Bit-for-bit reproducibility job in CI.  Ubuntu and Windows run the same seed
  in the pinned environment and compare the result hash.
- PyPI trusted publishing and GitHub Container Registry publishing in the
  release workflow.
- README table checker `scripts/check_readme.py`.  Every results table in the
  README is compared with its generated report.
- Stable result hash helper `scripts/result_hash.py`.
- Distribution published on PyPI as `market-sim==1.0.0` and a compressed
  container image attached to the GitHub release.

### Changed

- Version 1.0.0 freezes the model.  No parameter or process is added.
- The suite has 338 tests and 99% branch coverage.

## [0.9.0] - 2026-11-23

### Added

- Additional facts against the benchmarks in
  `docs/additional_discrimination.md`.  DFA Hurst separates the model from
  GARCH with AUC 0.998, aggregational Gaussianity with 0.804, while leverage
  and gain/loss asymmetry do not separate the two.
- Bootstrap 95% percentile intervals for the discrimination AUCs in
  `docs/discrimination.md`.  The ACF(abs, 1) interval contains 0.5.
- `non_volume_metrics` helper for the four additional facts that do not need a
  volume series.

### Changed

- The suite has 320 tests and 99% branch coverage.

## [0.8.0] - 2026-11-23

### Added

- Discrimination analysis in `docs/discrimination.md`, with the AUC of each
  price statistic against GARCH and Gaussian, a 6 by 6 threshold grid, and the
  heatmap `docs/discrimination.png`.
- The grid shows the separation region: at kurtosis > 4 and tail ratio > 10 the
  model passes 50/50 seeds and GARCH 93/100, while at kurtosis > 5 the model
  passes 46/50 and GARCH falls to 5/100.

### Changed

- The suite has 312 tests and 99% branch coverage.

## [0.7.0] - 2026-11-23

### Added

- Strict criteria on the 50-seed hold-out in `docs/strict_criteria.md`, with
  Wilson intervals and the four seeds that fail the strict kurtosis threshold.
- Gaussian null distribution in `docs/null_distribution.md`, with the 5%, 50%
  and 95% quantiles of the five price statistics and the model percentile.
- Wilson intervals for the all-five benchmark pass rate and for the cross-seed
  block pass rates.
- Pinned reference CI job regenerates the baseline and compares it with
  `docs/baseline_metrics.json` at a relative tolerance of 1e-9.

### Changed

- The suite has 306 tests and 99% branch coverage.

## [0.6.1] - 2026-11-23

### Fixed

- Output hashes normalise CRLF line endings before hashing text files, so
  `scripts/check_hashes.py` passes on Linux, Windows and macOS checkouts.

### Changed

- The suite has 285 tests and 99% branch coverage.

## [0.6.0] - 2026-11-23

### Added

- Benchmark pass rates over 100 synthetic series per process in
  `docs/benchmark_rates.md`, with the original criteria and with stricter tail
  criteria.
- Cross-seed block stability in `docs/block_ensemble.md` and
  `docs/block_ensemble.csv`.  Twenty seeds and ten blocks per seed give 200
  blocks.
- Aggregational Gaussianity in the additional facts, with kurtosis at
  horizons 1, 5, 20 and 60.
- Output hash checker in `scripts/check_hashes.py` and a CI step.
- Pre-commit hooks for documentation links, versions, the README table, the API
  reference and the output hashes.
- A test that every `scripts/run_*.py` file is in the one-command reproduction.

### Changed

- The additional-facts table now has five rows and the model passes two.
- The README, model card and FAQ document the weak original tail thresholds and
  the stricter benchmark result.
- The suite has 284 tests and 99% branch coverage.

## [0.5.0] - 2026-11-23

### Added

- Block-stability analysis in `docs/stability.md` and `docs/stability.csv`.  The
  baseline window is split into ten contiguous blocks and the six statistics
  are recomputed inside each block.
- Version consistency checker in `scripts/check_versions.py` and a CI step.
- README results table checker in `scripts/check_results.py` and a CI step.
- Generated API reference in `docs/api.md` with
  `scripts/build_api_docs.py --check` in CI.
- One-command reproduction in `scripts/reproduce_all.py`.
- Data dictionary, architecture and FAQ documents.

### Changed

- The public API exports the stability functions.
- The quality job checks documentation links, versions, README values and the
  API reference.
- The suite has 261 tests and 99% branch coverage.

## [0.4.1] - 2026-11-23

### Fixed

- The release workflow installs the built wheel before extracting the release
  notes, so the notes script has its runtime dependencies.

## [0.4.0] - 2026-11-23

### Added

- Finite-sample sensitivity at 10,000, 50,000, 100,000 and 200,000 steps in
  `docs/sample_size.md`.
- Price-gap and volume diagnostics in `docs/price_volume.md`.
- Documentation link checker in `scripts/check_docs.py`.
- Release workflow that builds the distribution and creates a GitHub release
  from the matching `CHANGELOG.md` section.
- Pinned reference constraints in `constraints-reference.txt` and a CI
  reference job.
- `Dockerfile` and a container smoke test in CI.

### Changed

- Coverage gate raised to 98%. The suite has 225 tests and 99% branch coverage.
- README and model card include the sample-size, price-volume and container
  analyses.

## [0.3.0] - 2026-11-22

### Added

- Component ablation study in `docs/ablations.md`.
- Full one-at-a-time sensitivity over 32 variants in
  `docs/sensitivity_full.md`.
- Threshold sensitivity over the per-seed metrics in `docs/thresholds.md`.
- 50-seed extended hold-out with a Wilson interval in
  `docs/robustness_50.md`.
- Synthetic benchmarks against Gaussian, Student-t and GARCH(1,1) returns in
  `docs/benchmarks.md`.
- Wall-clock performance benchmark in `docs/performance.md`.
- `scripts/compare_real_data.py` for user-supplied return or price series.
- Pre-commit configuration for ruff, ruff-format and mypy.

### Changed

- The README and model card now state that a noise-only ablation passes all
  six rows and that GARCH(1,1) also passes the five price facts.
- The test suite has 191 tests and 96% branch coverage.

## [0.2.0] - 2026-11-22

### Added

- Command-line interface with `simulate`, `figures`, `ensemble` and `version`.
- Console script `market-sim` and `python -m market_sim` entry point.
- Multi-seed robustness runner and a 20-seed hold-out report.
- Moving-block bootstrap with confidence intervals and `docs/inference.md`.
- Parameter robustness map with `docs/phase_diagram.md`.
- Additional stylized facts and an honest failure report in
  `docs/additional_facts.md`.
- Property-based tests with Hypothesis.
- Model card, reproducibility manifest and output hashes.
- Dependabot configuration for pip and GitHub Actions.
- Quality gates for lint, format, strict typing, coverage, build and wheel
  installation.
- End-to-end CI job that runs the full 101,000-step baseline, builds the
  figures and runs a 3-seed ensemble.

### Changed

- Numerical routines normalise by the maximum absolute deviation to avoid
  underflow on very small scales.
- CI matrix covers Python 3.12, 3.13 and 3.14 on Ubuntu and Windows.

### Fixed

- Kurtosis and autocorrelation no longer return NaN for series with an
  extremely small scale.

## [0.1.0] - 2026-11-22

### Added

- Heterogeneous agent model with fundamentalists, chartists and noise traders.
- Persistent activity state with memory-dependent AR(1) persistence.
- Linear price impact, gross-demand volume and reproducible seed handling.
- Five stylized-fact statistics with explicit thresholds.
- Baseline run over 101,000 steps and 100,000 analysed observations.
- Price, return-histogram and autocorrelation figures.
- Tests for reproducibility, hand-built statistics, edge cases and extreme
  parameters.
- CI on Ubuntu and Windows.
- MIT license.
