from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_release_workflow_contains_required_release_jobs() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    for job_name in (
        "validate:",
        "quality:",
        "build-python:",
        "sign-artifacts:",
        "verify-install:",
        "docker:",
        "publish-testpypi:",
        "publish-pypi:",
        "github-release:",
        "deploy-docs:",
    ):
        assert job_name in workflow


def test_release_workflow_uses_trusted_publishing_and_signing() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "sigstore/gh-action-sigstore-python@v3.2.0" in workflow
    assert "id-token: write" in workflow
    assert "cyclonedx-py environment" in workflow
    assert "sha256sum * > SHA256SUMS" in workflow


def test_pypi_publish_uses_distribution_only_artifact() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    publish_section = workflow.split("publish-testpypi:", maxsplit=1)[1]
    publish_section = publish_section.split("github-release:", maxsplit=1)[0]

    assert "name: python-distributions" in publish_section
    assert "name: signed-release-artifacts" not in publish_section
