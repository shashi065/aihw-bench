"""Prepare semantic version metadata and changelog entries for a release."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

try:
    from scripts.check_release_version import validate_tag
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.check_release_version import validate_tag

PROJECT_VERSION_PATTERN = re.compile(r'(?m)^version = "(?P<version>[^"]+)"$')
RUNTIME_VERSION_PATTERN = re.compile(r'(?m)^__version__ = "(?P<version>[^"]+)"$')


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version, for example 1.0.0.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Release date.")
    parser.add_argument("--pyproject", default="pyproject.toml", help="Path to pyproject.toml.")
    parser.add_argument(
        "--version-file",
        default="src/aihw_bench/_version.py",
        help="Path to the runtime package version module.",
    )
    parser.add_argument("--changelog", default="CHANGELOG.md", help="Path to CHANGELOG.md.")
    return parser.parse_args()


def replace_project_version(pyproject: str, version: str) -> str:
    """Return pyproject text with project.version replaced."""
    replacement = f'version = "{version}"'
    updated, count = PROJECT_VERSION_PATTERN.subn(replacement, pyproject, count=1)
    if count != 1:
        raise ValueError("pyproject.toml must contain exactly one project.version line.")
    return updated


def replace_runtime_version(version_file: str, version: str) -> str:
    """Return _version.py text with __version__ replaced."""
    replacement = f'__version__ = "{version}"'
    updated, count = RUNTIME_VERSION_PATTERN.subn(replacement, version_file, count=1)
    if count != 1:
        raise ValueError("_version.py must contain exactly one __version__ line.")
    return updated


def release_heading(version: str, release_date: str) -> str:
    """Return the changelog heading for a release."""
    return f"## [{version}] - {release_date}"


def insert_changelog_release(
    changelog: str,
    *,
    version: str,
    release_date: str,
) -> str:
    """Move the Unreleased section into a dated release section."""
    heading = release_heading(version, release_date)
    if heading in changelog or f"## [{version}]" in changelog:
        return changelog
    marker = "## [Unreleased]"
    if marker not in changelog:
        raise ValueError("CHANGELOG.md must contain an Unreleased section.")
    return changelog.replace(marker, f"{marker}\n\n{heading}", 1)


def prepare_release_files(
    *,
    version: str,
    release_date: str,
    pyproject_path: Path,
    version_file_path: Path,
    changelog_path: Path,
) -> None:
    """Update project metadata and changelog for a release."""
    validate_tag(f"v{version}")
    pyproject_path.write_text(
        replace_project_version(pyproject_path.read_text(encoding="utf-8"), version),
        encoding="utf-8",
    )
    version_file_path.write_text(
        replace_runtime_version(version_file_path.read_text(encoding="utf-8"), version),
        encoding="utf-8",
    )
    changelog_path.write_text(
        insert_changelog_release(
            changelog_path.read_text(encoding="utf-8"),
            version=version,
            release_date=release_date,
        ),
        encoding="utf-8",
    )


def main() -> int:
    """Prepare release files."""
    args = parse_args()
    prepare_release_files(
        version=args.version,
        release_date=args.date,
        pyproject_path=Path(args.pyproject),
        version_file_path=Path(args.version_file),
        changelog_path=Path(args.changelog),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
