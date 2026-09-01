import aihw_bench

STABLE_PUBLIC_EXPORTS = {
    "BenchmarkRequest",
    "BenchmarkService",
    "BenchmarkSession",
    "Configuration",
    "Metric",
    "ModelMetadata",
    "PluginManager",
    "PluginManifest",
    "PluginRegistration",
    "RuntimeExecutionError",
    "__version__",
}


def test_public_api_contains_stable_v1_exports() -> None:
    assert set(aihw_bench.__all__) >= STABLE_PUBLIC_EXPORTS


def test_runtime_version_matches_current_release() -> None:
    assert aihw_bench.__version__ == "2.0.1"
