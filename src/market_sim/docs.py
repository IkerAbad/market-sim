"""Check local Markdown links and required documentation sections."""

from __future__ import annotations

import re
from pathlib import Path

LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")
MARKDOWN_FILES = (
    "README.md",
    "MODEL_CARD.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
)
DOCS_DIR = "docs"


def markdown_files(root: Path) -> list[Path]:
    """Return the Markdown files that participate in the check."""
    files = [root / name for name in MARKDOWN_FILES if (root / name).exists()]
    docs = root / DOCS_DIR
    if docs.exists():
        files.extend(sorted(docs.glob("*.md")))
    return files


def check_file(path: Path, root: Path) -> list[str]:
    """Check one Markdown file for broken local links and placeholders."""
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for match in LINK.finditer(text):
        target = match.group(1).strip()
        if not target or target.startswith(SKIP_PREFIXES):
            continue
        target = target.split("#", 1)[0].split("?", 1)[0]
        if not target:
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            errors.append(f"{path}: link leaves the repository: {target}")
            continue
        if not resolved.exists():
            errors.append(f"{path}: missing link target: {target}")
    for marker in ("TODO", "FIXME"):
        if marker in text:
            errors.append(f"{path}: contains {marker}")
    return errors


def check_docs(root: Path) -> list[str]:
    """Check every documentation file under ``root``."""
    errors: list[str] = []
    readme = root / "README.md"
    if readme.exists() and "## Español" not in readme.read_text(encoding="utf-8"):
        errors.append("README.md: missing ## Español section")
    for path in markdown_files(root):
        errors.extend(check_file(path, root))
    return errors
