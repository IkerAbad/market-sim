"""Check that every version string in the repository agrees."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _pyproject_version(root: Path) -> str:
    with (root / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return str(data["project"]["version"])


def _citation_version(root: Path) -> str:
    match = re.search(r"^version:\s*(\S+)\s*$", _read(root / "CITATION.cff"), re.MULTILINE)
    if match is None:
        raise ValueError("CITATION.cff has no version field")
    return match.group(1)


def _model_card_version(root: Path) -> str:
    match = re.search(r"^- Version:\s*(\S+)\s*$", _read(root / "MODEL_CARD.md"), re.MULTILINE)
    if match is None:
        raise ValueError("MODEL_CARD.md has no version line")
    return match.group(1)


def _changelog_version(root: Path) -> str:
    versions = re.findall(r"^## \[([^\]]+)\]", _read(root / "CHANGELOG.md"), re.MULTILINE)
    for version in versions:
        text = str(version)
        if text != "Unreleased":
            return text
    raise ValueError("CHANGELOG.md has no released version")


def check_versions(root: Path, package_version: str | None = None) -> list[str]:
    """Return a list of version mismatches under ``root``."""
    if package_version is None:
        from . import __version__ as package_version
    expected = _pyproject_version(root)
    errors: list[str] = []
    if package_version != expected:
        errors.append(
            f"src/market_sim/__init__.py: {package_version} != pyproject.toml: {expected}"
        )
    for label, value in (
        ("CITATION.cff", _citation_version(root)),
        ("MODEL_CARD.md", _model_card_version(root)),
        ("CHANGELOG.md", _changelog_version(root)),
    ):
        if value != expected:
            errors.append(f"{label}: {value} != pyproject.toml: {expected}")
    return errors
