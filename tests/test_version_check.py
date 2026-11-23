from __future__ import annotations

from pathlib import Path

import pytest

from market_sim.version_check import check_versions

ROOT = Path(__file__).resolve().parents[1]


def _write_metadata(tmp_path: Path, version: str = "1.0.0") -> None:
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "x"\nversion = "{version}"\n', encoding="utf-8"
    )
    (tmp_path / "CITATION.cff").write_text(f"version: {version}\n", encoding="utf-8")
    (tmp_path / "MODEL_CARD.md").write_text(f"- Version: {version}\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        f"## [Unreleased]\n\n## [{version}] - 2026-01-01\n", encoding="utf-8"
    )


def test_repository_versions_agree() -> None:
    assert check_versions(ROOT) == []


def test_version_mismatch_is_reported(tmp_path) -> None:
    _write_metadata(tmp_path)
    assert check_versions(tmp_path, package_version="1.0.0") == []
    errors = check_versions(tmp_path, package_version="0.9.0")
    assert any("__init__.py" in error for error in errors)


def test_file_version_mismatch_is_reported(tmp_path) -> None:
    _write_metadata(tmp_path)
    (tmp_path / "CITATION.cff").write_text("version: 0.9.0\n", encoding="utf-8")
    errors = check_versions(tmp_path, package_version="1.0.0")
    assert any("CITATION.cff" in error for error in errors)


def test_changelog_without_release_is_reported(tmp_path) -> None:
    _write_metadata(tmp_path)
    (tmp_path / "CHANGELOG.md").write_text("## [Unreleased]\n", encoding="utf-8")
    with pytest.raises(ValueError):
        check_versions(tmp_path, package_version="1.0.0")


def test_missing_citation_version_is_reported(tmp_path) -> None:
    _write_metadata(tmp_path)
    (tmp_path / "CITATION.cff").write_text("title: x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        check_versions(tmp_path, package_version="1.0.0")


def test_missing_model_card_version_is_reported(tmp_path) -> None:
    _write_metadata(tmp_path)
    (tmp_path / "MODEL_CARD.md").write_text("# Model\n", encoding="utf-8")
    with pytest.raises(ValueError):
        check_versions(tmp_path, package_version="1.0.0")
