from pathlib import Path

import pytest
from scripts.check_release_version import (
    read_project_version,
    read_runtime_version,
    validate_changelog,
    validate_tag,
    validate_version_is_not_placeholder,
)
from scripts.generate_release_notes import extract_changelog_section
from scripts.prepare_release import (
    insert_changelog_release,
    replace_project_version,
    replace_runtime_version,
)


def test_validate_tag_returns_version() -> None:
    assert validate_tag("v0.1.0") == "0.1.0"


def test_validate_tag_accepts_prerelease_version() -> None:
    assert validate_tag("v1.2.3-rc.1") == "1.2.3-rc.1"


def test_validate_tag_rejects_non_semver_tag() -> None:
    with pytest.raises(ValueError, match="semantic"):
        validate_tag("release-1.2")


def test_read_project_version(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")

    assert read_project_version(pyproject) == "1.2.3"


def test_read_runtime_version(tmp_path: Path) -> None:
    version_file = tmp_path / "_version.py"
    version_file.write_text('__version__ = "1.2.3"\n', encoding="utf-8")

    assert read_runtime_version(version_file) == "1.2.3"


def test_validate_changelog_accepts_bracketed_release(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## [1.2.3]\n\n- Release.\n", encoding="utf-8")

    validate_changelog(changelog, "1.2.3")


def test_validate_version_rejects_placeholder() -> None:
    with pytest.raises(ValueError, match=r"0\.0\.0"):
        validate_version_is_not_placeholder("0.0.0")


def test_extract_changelog_section_returns_version_body() -> None:
    changelog = "# Changelog\n\n## [1.2.3]\n\n### Added\n\n- Release.\n\n## [1.2.2]\n"

    assert extract_changelog_section(changelog, "1.2.3") == "### Added\n\n- Release."


def test_replace_project_version_updates_single_version() -> None:
    pyproject = '[project]\nname = "aihw-bench"\nversion = "0.0.0"\n'

    assert 'version = "0.1.0"' in replace_project_version(pyproject, "0.1.0")


def test_replace_runtime_version_updates_dunder_version() -> None:
    version_file = '"""Package version metadata."""\n\n__version__ = "0.0.0"\n'

    assert '__version__ = "1.0.0"' in replace_runtime_version(version_file, "1.0.0")


def test_insert_changelog_release_adds_dated_section() -> None:
    changelog = "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- Feature.\n"

    updated = insert_changelog_release(changelog, version="0.1.0", release_date="2026-07-29")

    assert "## [Unreleased]\n\n## [0.1.0] - 2026-07-29" in updated
