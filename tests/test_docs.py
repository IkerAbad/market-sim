from __future__ import annotations

from pathlib import Path

from market_sim.docs import check_docs

ROOT = Path(__file__).resolve().parents[1]


def test_repository_docs_are_valid() -> None:
    assert check_docs(ROOT) == []


def test_missing_link_is_reported(tmp_path) -> None:
    (tmp_path / "README.md").write_text(
        "# Test\n\n## Español\n\n[missing](docs/missing.md)\n",
        encoding="utf-8",
    )
    errors = check_docs(tmp_path)
    assert any("missing link target" in error for error in errors)


def test_external_links_are_ignored(tmp_path) -> None:
    (tmp_path / "README.md").write_text(
        "# Test\n\n## Español\n\n[site](https://example.com)\n",
        encoding="utf-8",
    )
    assert check_docs(tmp_path) == []


def test_placeholder_is_reported(tmp_path) -> None:
    (tmp_path / "README.md").write_text(
        "# Test\n\n## Español\n\nTODO: finish\n",
        encoding="utf-8",
    )
    errors = check_docs(tmp_path)
    assert any("contains TODO" in error for error in errors)


def test_missing_spanish_section_is_reported(tmp_path) -> None:
    (tmp_path / "README.md").write_text("# Test\n", encoding="utf-8")
    errors = check_docs(tmp_path)
    assert "README.md: missing ## Español section" in errors
