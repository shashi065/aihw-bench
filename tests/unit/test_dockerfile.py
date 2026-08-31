from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_DOCKERFILE_SMOKE_CHECKS = 2


def test_dockerfile_builds_wheel_before_runtime_image() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim AS builder" in dockerfile
    assert "python -m build --wheel" in dockerfile
    assert "COPY --from=builder /opt/aihw-bench /opt/aihw-bench" in dockerfile


def test_dockerfile_smoke_checks_cli_entrypoint() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert dockerfile.count("aihw-bench version") >= EXPECTED_DOCKERFILE_SMOKE_CHECKS
    assert 'ENTRYPOINT ["aihw-bench"]' in dockerfile
    assert 'CMD ["--help"]' in dockerfile
