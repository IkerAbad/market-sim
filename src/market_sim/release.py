"""Extract one release section from CHANGELOG.md."""

from __future__ import annotations

import re


def extract_release_notes(changelog: str, version: str) -> str:
    """Return the section for ``version`` without the trailing sections."""
    clean = version.strip()
    if clean.startswith("v"):
        clean = clean[1:]
    pattern = re.compile(
        rf"^## \[{re.escape(clean)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(changelog)
    if match is None:
        available = re.findall(r"^## \[([^\]]+)\]", changelog, flags=re.MULTILINE)
        raise ValueError(
            f"version {clean!r} not found in the changelog. "
            f"Available versions: {', '.join(available)}"
        )
    heading = changelog[match.start() :].splitlines()[0]
    body = match.group(1).strip()
    return f"{heading}\n\n{body}\n"
