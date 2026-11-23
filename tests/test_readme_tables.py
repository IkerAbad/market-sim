from __future__ import annotations

from market_sim import readme_tables
from market_sim.readme_tables import (
    check_readme_tables,
    numeric_values,
    parse_tables,
    table_values,
)


def test_numeric_values() -> None:
    assert numeric_values("5.488, -0.004945, 3/3, 100.0%") == [
        5.488,
        -0.004945,
        "3/3",
        1.0,
    ]


def test_parse_tables() -> None:
    markdown = "# One\n\n| A | B |\n| --- | ---: |\n| 1 | 2 |\n\n## Two\n\n| C |\n| --- |\n| 3 |\n"
    tables = parse_tables(markdown)
    assert [table.heading for table in tables] == ["One", "Two"]
    assert table_values(tables[0]) == [1.0, 2.0]


def test_table_with_only_separator_is_ignored() -> None:
    markdown = "# One\n\n| --- | --- |\n"
    assert parse_tables(markdown) == []


def test_unmapped_heading_is_skipped(tmp_path) -> None:
    (tmp_path / "README.md").write_text("# Other\n\n| A |\n| --- |\n| 1 |\n", encoding="utf-8")
    assert check_readme_tables(tmp_path) == []


def test_markdown_source(tmp_path) -> None:
    (tmp_path / "README.md").write_text(
        "# Robustness across seeds\n\n| A |\n| --- |\n| 5 |\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "robustness.md").write_text("| A |\n| --- |\n| 5 |\n", encoding="utf-8")
    assert check_readme_tables(tmp_path) == []


def test_english_source_and_cache(tmp_path, monkeypatch) -> None:
    monkeypatch.setitem(readme_tables.SECTION_SOURCES, "Otra", ("english", "Results"))
    (tmp_path / "README.md").write_text(
        "# Results\n\n| A |\n| --- |\n| 1 |\n\n"
        "# Resultados\n\n| A |\n| --- |\n| 1 |\n\n"
        "# Otra\n\n| A |\n| --- |\n| 1 |\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "baseline_metrics.json").write_text(
        '{"metrics": {"a": 1.0}}', encoding="utf-8"
    )
    assert check_readme_tables(tmp_path) == []


def test_missing_english_source_is_reported(tmp_path) -> None:
    (tmp_path / "README.md").write_text("# Resultados\n\n| A |\n| --- |\n| 1 |\n", encoding="utf-8")
    errors = check_readme_tables(tmp_path)
    assert any("English table" in error for error in errors)


def test_fraction_mismatch_is_reported(tmp_path) -> None:
    (tmp_path / "README.md").write_text("# Results\n\n| A |\n| --- |\n| 3/3 |\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "baseline_metrics.json").write_text(
        '{"metrics": {"a": 1.0}}', encoding="utf-8"
    )
    errors = check_readme_tables(tmp_path)
    assert any("3/3" in error for error in errors)


def test_check_passes(tmp_path) -> None:
    (tmp_path / "README.md").write_text(
        "# Results\n\n| A | B |\n| --- | ---: |\n| 1 | 2 |\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "baseline_metrics.json").write_text(
        '{"metrics": {"a": 1.0, "b": 2.0}}', encoding="utf-8"
    )
    assert check_readme_tables(tmp_path) == []


def test_missing_value_is_reported(tmp_path) -> None:
    (tmp_path / "README.md").write_text(
        "# Results\n\n| A | B |\n| --- | ---: |\n| 1 | 9 |\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "baseline_metrics.json").write_text(
        '{"metrics": {"a": 1.0, "b": 2.0}}', encoding="utf-8"
    )
    errors = check_readme_tables(tmp_path)
    assert any("9.0" in error for error in errors)


def test_missing_source_is_reported(tmp_path) -> None:
    (tmp_path / "README.md").write_text(
        "# Results\n\n| A |\n| --- |\n| 1 |\n",
        encoding="utf-8",
    )
    errors = check_readme_tables(tmp_path)
    assert any("missing" in error for error in errors)
