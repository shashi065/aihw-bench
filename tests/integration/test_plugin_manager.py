from __future__ import annotations

from aihw_bench.application import (
    PluginDiscovery,
    PluginManager,
    PluginManifest,
    PluginProviderKind,
    PluginRegistration,
)
from aihw_bench.domain.models import Configuration


def test_plugin_manager_discovers_registers_and_activates_objects() -> None:
    lifecycle: list[str] = []
    manifest = PluginManifest(
        name="integration-plugin",
        version="0.1.0",
        package="integration-plugin-package",
        description="Integration plugin",
        providers=(PluginProviderKind.METRICS, PluginProviderKind.EXPORTERS),
    )

    def plugin_factory() -> PluginRegistration:
        registration = PluginRegistration.from_manifest(
            manifest,
            providers={
                PluginProviderKind.METRICS: {"integration_metric": object()},
                PluginProviderKind.EXPORTERS: {"integration_exporter": object()},
            },
        )
        registration.validate = lambda context: lifecycle.append(context.configuration.profile)
        registration.activate = lambda context: lifecycle.append("active")
        registration.deactivate = lambda context: lifecycle.append("inactive")
        return registration

    discovery = PluginDiscovery()
    manager = PluginManager(configuration=Configuration(), discovery=discovery)
    registry = manager.load(discovery.discover_objects([plugin_factory]))

    assert "integration_metric" in registry.providers_for("metrics")
    assert "integration_exporter" in registry.providers_for("exporters")
    assert registry.plugin_metadata()[0].status == "active"
    assert lifecycle == ["default", "active"]

    registry.deactivate_all()

    assert registry.plugin_metadata()[0].status == "available"
    assert lifecycle == ["default", "active", "inactive"]
