from __future__ import annotations

import pytest

from market_sim.release import extract_release_notes

CHANGELOG = """# Changelog

## [Unreleased]

## [0.4.0] - 2026-11-23

### Added

- New release workflow.

## [0.3.0] - 2026-11-22

### Added

- Previous feature.
"""


def test_extract_release_notes() -> None:
    notes = extract_release_notes(CHANGELOG, "v0.4.0")
    assert "## [0.4.0]" in notes
    assert "New release workflow" in notes
    assert "Previous feature" not in notes


def test_extract_without_v_prefix() -> None:
    notes = extract_release_notes(CHANGELOG, "0.4.0")
    assert "New release workflow" in notes


def test_missing_version_raises() -> None:
    with pytest.raises(ValueError, match="Available versions"):
        extract_release_notes(CHANGELOG, "9.9.9")
