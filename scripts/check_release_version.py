"""Validate semantic release tag, package metadata, and changelog alignment."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

SEMVER_TAG_PATTERN = re.compile(
    r"^v(?P<version>"
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9A-Za-z-][0-9A-Za-z-]*))*)?"
    r")$"
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Git tag, for example v1.0.0.")
    parser.add_argument("--pyproject", default="pyproject.toml", help="Path to pyproject.toml.")
    parser.add_argument(
        "--version-file",
        default="src/aihw_bench/_version.py",
        help="Path to the runtime package version module.",
    )
    parser.add_argument("--changelog", default="CHANGELOG.md", help="Path to CHANGELOG.md.")
    return parser.parse_args()


def read_project_version(pyproject_path: Path) -> str:
    """Read the project version from PEP 621 metadata."""
    with pyproject_path.open("rb") as file:
        data = tomllib.load(file)
    try:
        version = data["project"]["version"]
    except KeyError as exc:
        raise ValueError("pyproject.toml must define project.version.") from exc
    if not isinstance(version, str):
        raise ValueError("project.version must be a string.")
    return version


def validate_tag(tag: str) -> str:
    """Return the version encoded by a release tag."""
    match = SEMVER_TAG_PATTERN.match(tag)
    if match is None:
        raise ValueError(f"Release tag must use semantic format vMAJOR.MINOR.PATCH: {tag}")
    return tag.removeprefix("v")


def validate_changelog(changelog_path: Path, version: str) -> None:
    """Ensure the changelog contains an entry for the release version."""
    changelog = changelog_path.read_text(encoding="utf-8")
    accepted_headings = (f"## [{version}]", f"## {version}")
    if not any(heading in changelog for heading in accepted_headings):
        raise ValueError(f"CHANGELOG.md must contain a release section for {version}.")


def read_runtime_version(version_file_path: Path) -> str:
    """Read __version__ from the runtime package version file."""
    namespace: dict[str, str] = {}
    exec(version_file_path.read_text(encoding="utf-8"), {}, namespace)
    version = namespace.get("__version__")
    if not isinstance(version, str):
        raise ValueError("_version.py must define __version__ as a string.")
    return version


def validate_version_is_not_placeholder(version: str) -> None:
    """Reject the repository bootstrap version for publishable releases."""
    if version == "0.0.0":
        raise ValueError("project.version must be bumped from 0.0.0 before release.")


def main() -> int:
    """Run release metadata validation."""
    args = parse_args()
    tag_version = validate_tag(args.tag)
    project_version = read_project_version(Path(args.pyproject))
    runtime_version = read_runtime_version(Path(args.version_file))

    if tag_version != project_version:
        raise ValueError(
            f"Release tag {args.tag} does not match project.version {project_version}."
        )
    if tag_version != runtime_version:
        raise ValueError(
            f"Release tag {args.tag} does not match runtime __version__ {runtime_version}."
        )
    validate_version_is_not_placeholder(project_version)

    validate_changelog(Path(args.changelog), tag_version)
    print(f"Release metadata validated for {args.tag}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(f"release validation failed: {error}", file=sys.stderr)
        raise SystemExit(2) from error
