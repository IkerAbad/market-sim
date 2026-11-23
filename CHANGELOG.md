# Changelog

All notable changes to this project are documented in this file.

The format follows Keep a Changelog and the project uses semantic versioning.

## [Unreleased]

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
