from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import ValidationError as PydanticValidationError

from aihw_bench.application import (
    CORE_PLUGIN_API_VERSION,
    PluginContext,
    PluginDiscovery,
    PluginLifecycleState,
    PluginManifest,
    PluginProviderKind,
    PluginRegistration,
    PluginRegistry,
)
from aihw_bench.domain.errors import PluginError
from aihw_bench.domain.models import Configuration, PluginsConfig


def _registration(
    name: str,
    *,
    providers: dict[PluginProviderKind | str, dict[str, object]] | None = None,
    dependencies: tuple[str, ...] = (),
    api_version: str = CORE_PLUGIN_API_VERSION,
) -> PluginRegistration:
    provider_kinds = tuple(
        kind if isinstance(kind, PluginProviderKind) else PluginProviderKind(kind)
        for kind in (providers or {})
    )
    manifest = PluginManifest(
        name=name,
        version="0.1.0",
        api_version=api_version,
        package=f"{name}-package",
        description=f"{name} plugin",
        providers=provider_kinds,
        dependencies=dependencies,
    )
    return PluginRegistration.from_manifest(manifest, providers=providers)


def test_registry_registers_metric_provider() -> None:
    provider = object()
    registry = PluginRegistry()

    registry.register(
        _registration(
            "metrics-plugin",
            providers={PluginProviderKind.METRICS: {"custom_latency": provider}},
        )
    )

    assert registry.states["metrics-plugin"] is PluginLifecycleState.REGISTERED
    assert registry.provider(PluginProviderKind.METRICS, "custom_latency") is provider
    assert registry.providers_for("metrics") == {"custom_latency": provider}
    assert registry.plugin_metadata()[0].status == "available"


def test_registry_skips_disabled_plugins() -> None:
    configuration = Configuration(plugins=PluginsConfig(disabled=["disabled-plugin"]))
    registry = PluginRegistry(configuration=configuration)

    registry.register(
        _registration(
            "disabled-plugin",
            providers={PluginProviderKind.EXPORTERS: {"custom": object()}},
        )
    )

    assert registry.states["disabled-plugin"] is PluginLifecycleState.DISABLED
    assert registry.providers_for(PluginProviderKind.EXPORTERS) == {}
    assert registry.plugin_metadata()[0].status == "disabled"


def test_registry_uses_enabled_allowlist() -> None:
    configuration = Configuration(plugins=PluginsConfig(enabled=["allowed-plugin"]))
    registry = PluginRegistry(configuration=configuration)

    registry.register(
        _registration(
            "other-plugin",
            providers={PluginProviderKind.REPORTS: {"other": object()}},
        )
    )

    assert registry.states["other-plugin"] is PluginLifecycleState.DISABLED


def test_registry_isolates_incompatible_plugin() -> None:
    registry = PluginRegistry()

    registry.register(_registration("old-plugin", api_version="0.9"))

    assert registry.states["old-plugin"] is PluginLifecycleState.FAILED
    assert registry.diagnostics[0].code == "plugin.registration_failed"
    assert registry.plugin_metadata()[0].diagnostics


def test_registry_raises_for_strict_plugin_failure() -> None:
    configuration = Configuration(plugins=PluginsConfig(strict=True))
    registry = PluginRegistry(configuration=configuration)

    with pytest.raises(PluginError, match="strict mode"):
        registry.register(_registration("old-plugin", api_version="0.9"))


def test_registry_resolves_dependencies_before_dependents() -> None:
    registry = PluginRegistry()
    base = _registration(
        "base-plugin",
        providers={PluginProviderKind.HARDWARE: {"base-hardware": object()}},
    )
    dependent = _registration(
        "dependent-plugin",
        providers={PluginProviderKind.MODELS: {"model-loader": object()}},
        dependencies=("base-plugin",),
    )

    registry.register_many([dependent, base])

    assert registry.states["base-plugin"] is PluginLifecycleState.REGISTERED
    assert registry.states["dependent-plugin"] is PluginLifecycleState.REGISTERED


def test_registry_reports_missing_dependencies() -> None:
    registry = PluginRegistry()

    registry.register_many(
        [
            _registration(
                "dependent-plugin",
                providers={PluginProviderKind.MODELS: {"model-loader": object()}},
                dependencies=("missing-plugin",),
            )
        ]
    )

    assert registry.states["dependent-plugin"] is PluginLifecycleState.FAILED
    assert registry.diagnostics[0].code == "plugin.dependency_resolution_failed"


def test_registry_rejects_duplicate_provider_names() -> None:
    registry = PluginRegistry()

    registry.register(
        _registration("first", providers={PluginProviderKind.REPORTS: {"json": object()}})
    )
    registry.register(
        _registration("second", providers={PluginProviderKind.REPORTS: {"json": object()}})
    )

    assert registry.states["second"] is PluginLifecycleState.FAILED
    assert len(registry.providers_for("reports")) == 1


def test_registry_reports_missing_provider_lookup() -> None:
    registry = PluginRegistry()

    with pytest.raises(PluginError, match="not registered"):
        registry.provider("metrics", "missing")


def test_registry_rejects_undeclared_provider_kind() -> None:
    registry = PluginRegistry()
    manifest = PluginManifest(
        name="bad-provider",
        version="0.1.0",
        package="bad-provider-package",
        description="Bad provider",
        providers=(PluginProviderKind.METRICS,),
    )

    registry.register(
        PluginRegistration.from_manifest(
            manifest,
            providers={PluginProviderKind.REPORTS: {"report": object()}},
        )
    )

    assert registry.states["bad-provider"] is PluginLifecycleState.FAILED
    assert "not declared" in registry.diagnostics[0].cause


def test_registry_rejects_unknown_provider_kind() -> None:
    registry = PluginRegistry()

    with pytest.raises(PluginError, match="not supported"):
        registry.providers_for("unknown")


def test_manifest_rejects_blank_dependency() -> None:
    with pytest.raises(PydanticValidationError, match="dependencies"):
        PluginManifest(
            name="blank-dependency",
            version="0.1.0",
            package="blank-dependency-package",
            description="Bad dependency",
            dependencies=(" ",),
        )


def test_lifecycle_callbacks_are_isolated() -> None:
    calls: list[str] = []

    def activate(context: PluginContext) -> None:
        calls.append(context.configuration.profile)

    registry = PluginRegistry()
    registration = _registration(
        "lifecycle-plugin",
        providers={PluginProviderKind.CLI_COMMANDS: {"hello": object()}},
    )
    registration.activate = activate

    registry.register(registration)
    registry.activate_all()

    assert registry.states["lifecycle-plugin"] is PluginLifecycleState.ACTIVE
    assert calls == ["default"]


def test_lifecycle_failure_is_recorded_without_losing_registered_providers() -> None:
    def activate(context: PluginContext) -> None:
        raise RuntimeError("optional runtime missing")

    registry = PluginRegistry()
    registration = _registration(
        "failing-lifecycle-plugin",
        providers={PluginProviderKind.EXPORTERS: {"custom": object()}},
    )
    registration.activate = activate

    registry.register(registration)
    registry.activate_all()

    assert registry.states["failing-lifecycle-plugin"] is PluginLifecycleState.FAILED
    assert registry.providers_for("exporters")
    assert registry.diagnostics[0].metadata["stage"] == "activation"


def test_deactivation_failure_is_recorded() -> None:
    def deactivate(context: PluginContext) -> None:
        raise RuntimeError("shutdown failed")

    registry = PluginRegistry()
    registration = _registration(
        "deactivate-plugin",
        providers={PluginProviderKind.EXPORTERS: {"custom": object()}},
    )
    registration.deactivate = deactivate

    registry.register(registration)
    registry.activate_all()
    registry.deactivate_all()

    assert registry.states["deactivate-plugin"] is PluginLifecycleState.FAILED
    assert registry.diagnostics[0].metadata["stage"] == "deactivation"


def test_discovery_normalizes_manifest_registration_and_factory() -> None:
    manifest = PluginManifest(
        name="manifest-plugin",
        version="0.1.0",
        package="manifest-plugin-package",
        description="Manifest plugin",
        providers=(PluginProviderKind.METRICS,),
    )
    registration = _registration(
        "registration-plugin",
        providers={PluginProviderKind.REPORTS: {"summary": object()}},
    )

    discovered = PluginDiscovery().discover_objects(
        [manifest, registration, lambda: _registration("factory-plugin")]
    )

    assert [plugin.metadata.name for plugin in discovered] == [
        "manifest-plugin",
        "registration-plugin",
        "factory-plugin",
    ]


def test_discovery_records_invalid_plugin_object() -> None:
    discovery = PluginDiscovery()

    registrations = discovery.discover_objects([object()])

    assert registrations == []
    assert discovery.diagnostics[0].code == "plugin.discovery_failed"


def test_discovery_rejects_non_callable_register_attribute() -> None:
    discovery = PluginDiscovery()

    registrations = discovery.discover_objects([SimpleNamespace(register_plugin="not callable")])

    assert registrations == []
    assert "not callable" in discovery.diagnostics[0].cause


def test_discovery_strict_mode_raises_on_invalid_plugin_object() -> None:
    with pytest.raises(PluginError, match="strict mode"):
        PluginDiscovery(strict=True).discover_objects([object()])


def test_discovery_loads_entry_points(monkeypatch) -> None:
    registration = _registration("entry-point-plugin")
    fake_entry_point = SimpleNamespace(
        name="entry-point-plugin",
        load=lambda: registration,
    )
    monkeypatch.setattr(
        "aihw_bench.application.plugins.metadata.entry_points",
        lambda group: [fake_entry_point],
    )

    discovered = PluginDiscovery().discover_entry_points()

    assert discovered == [registration]
