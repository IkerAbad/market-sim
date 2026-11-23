from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import market_sim
from market_sim.api_docs import _summary, build_api_markdown, check_api_docs

ROOT = Path(__file__).resolve().parents[1]


def test_api_markdown_covers_public_names() -> None:
    markdown = build_api_markdown()
    for name in market_sim.__all__:
        assert f"`{name}`" in markdown


def test_api_markdown_accepts_explicit_package() -> None:
    markdown = build_api_markdown(market_sim)
    assert "`simulate`" in markdown


def test_summary_without_docstring() -> None:
    class Empty:
        pass

    assert _summary(Empty()) == ""


def test_signature_failure_is_handled() -> None:
    def broken() -> None:
        pass

    broken.__signature__ = "not a signature"  # type: ignore[attr-defined]
    package = SimpleNamespace(__all__=["broken"], broken=broken)
    markdown = build_api_markdown(package)
    assert "`broken`" in markdown


def test_repository_api_docs_are_current() -> None:
    assert check_api_docs(ROOT) == []


def test_missing_api_docs_are_reported(tmp_path) -> None:
    errors = check_api_docs(tmp_path)
    assert any("missing" in error for error in errors)


def test_stale_api_docs_are_reported(tmp_path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "api.md").write_text("old\n", encoding="utf-8")
    errors = check_api_docs(tmp_path)
    assert any("stale" in error for error in errors)
