# Changelog

All notable changes to this project are documented in this file.

The format follows Keep a Changelog and the project uses semantic versioning.

## [Unreleased]

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
