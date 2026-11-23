"""Check the committed output hashes in ``docs/reproducibility.md``."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROW_PATTERN = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*`([0-9A-Fa-f]{64})`\s*\|\s*$",
    re.MULTILINE,
)

TEXT_SUFFIXES = {".csv", ".json", ".md", ".txt"}

# Timing depends on the machine and cannot be byte-identical across runs.
ENVIRONMENT_DEPENDENT = {"docs/performance.csv"}


def parse_hash_table(text: str) -> list[tuple[str, str]]:
    """Return ``(path, sha256)`` pairs from the Markdown hash table."""
    return [(match.group(1), match.group(2).upper()) for match in ROW_PATTERN.finditer(text)]


def sha256_file(path: Path) -> str:
    """Return the uppercase SHA256 digest of a file.

    Text files are hashed with LF line endings so the digest does not depend
    on the checkout platform.  Binary files are hashed as they are.
    """
    data = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest().upper()


def check_hashes(root: Path) -> list[str]:
    """Return every missing file or hash mismatch in the committed table."""
    text = (root / "docs" / "reproducibility.md").read_text(encoding="utf-8")
    entries = parse_hash_table(text)
    if not entries:
        return ["docs/reproducibility.md has no hash rows"]
    errors: list[str] = []
    listed = {relative for relative, _ in entries}
    for path in sorted((root / "docs").iterdir()):
        if path.suffix in {".csv", ".json", ".png"}:
            relative = path.relative_to(root).as_posix()
            if relative in ENVIRONMENT_DEPENDENT:
                continue
            if relative not in listed:
                errors.append(f"{relative}: file has no hash row")
    for relative, expected in entries:
        path = root / relative
        if not path.exists():
            errors.append(f"{relative}: file is missing")
            continue
        actual = sha256_file(path)
        if actual != expected:
            errors.append(f"{relative}: {actual} != {expected}")
    return errors
