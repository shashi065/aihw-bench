"""Generate release notes from CHANGELOG.md with a git-log fallback."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

HEADING_PATTERN = re.compile(r"^## \[?(?P<version>[^\]\n]+)\]?", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version without the v prefix.")
    parser.add_argument("--changelog", default="CHANGELOG.md", help="Path to CHANGELOG.md.")
    parser.add_argument("--output", default="RELEASE_NOTES.md", help="Output release notes path.")
    return parser.parse_args()


def extract_changelog_section(changelog: str, version: str) -> str | None:
    """Return the body for one changelog version section."""
    matches = list(HEADING_PATTERN.finditer(changelog))
    for index, match in enumerate(matches):
        if match.group("version").strip() != version:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(changelog)
        body = changelog[start:end].strip()
        return body or None
    return None


def fallback_git_log() -> str:
    """Return recent commits when no changelog section is available."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--decorate", "--no-merges", "-20"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "Release notes were not available from CHANGELOG.md or git history."
    return result.stdout.strip() or "Release notes were not available from git history."


def generate_release_notes(changelog_path: Path, version: str) -> str:
    """Generate release notes for a version."""
    changelog = changelog_path.read_text(encoding="utf-8")
    return extract_changelog_section(changelog, version) or fallback_git_log()


def main() -> int:
    """Write release notes to disk."""
    args = parse_args()
    notes = generate_release_notes(Path(args.changelog), args.version)
    Path(args.output).write_text(notes.rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
