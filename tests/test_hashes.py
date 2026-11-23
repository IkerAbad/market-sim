from __future__ import annotations

from pathlib import Path

from market_sim.hashes import check_hashes, parse_hash_table, sha256_file

ROOT = Path(__file__).resolve().parents[1]


def test_repository_hashes_match() -> None:
    assert check_hashes(ROOT) == []


def test_parse_hash_table() -> None:
    text = "| `docs/a.csv` | `" + "A" * 64 + "` |\n"
    assert parse_hash_table(text) == [("docs/a.csv", "A" * 64)]


def test_hash_mismatch_is_reported(tmp_path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.csv").write_text("x\n", encoding="utf-8")
    digest = sha256_file(tmp_path / "docs" / "a.csv")
    (tmp_path / "docs" / "reproducibility.md").write_text(
        f"| `docs/a.csv` | `{digest}` |\n", encoding="utf-8"
    )
    assert check_hashes(tmp_path) == []
    (tmp_path / "docs" / "a.csv").write_text("y\n", encoding="utf-8")
    errors = check_hashes(tmp_path)
    assert any("docs/a.csv" in error for error in errors)


def test_missing_file_is_reported(tmp_path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "reproducibility.md").write_text(
        "| `docs/missing.csv` | `" + "A" * 64 + "` |\n", encoding="utf-8"
    )
    errors = check_hashes(tmp_path)
    assert any("missing" in error for error in errors)


def test_crlf_and_lf_hash_the_same(tmp_path) -> None:
    lf = tmp_path / "lf.csv"
    crlf = tmp_path / "crlf.csv"
    lf.write_bytes(b"a,b\n1,2\n")
    crlf.write_bytes(b"a,b\r\n1,2\r\n")
    assert sha256_file(lf) == sha256_file(crlf)


def test_unlisted_file_is_reported(tmp_path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.csv").write_text("x\n", encoding="utf-8")
    (tmp_path / "docs" / "reproducibility.md").write_text(
        "| `docs/a.csv` | `" + "A" * 64 + "` |\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "b.csv").write_text("y\n", encoding="utf-8")
    errors = check_hashes(tmp_path)
    assert any("no hash row" in error for error in errors)


def test_empty_table_is_reported(tmp_path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "reproducibility.md").write_text("# Empty\n", encoding="utf-8")
    errors = check_hashes(tmp_path)
    assert any("no hash rows" in error for error in errors)
