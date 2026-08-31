"""Plugin discovery, validation, registration, and lifecycle management."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from importlib import metadata
from typing import Any, Final, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aihw_bench.domain.errors import PluginError
from aihw_bench.domain.models import (
    Configuration,
    Diagnostic,
    DiagnosticSeverity,
    PluginMetadata,
)

CORE_PLUGIN_API_VERSION: Final[str] = "1.0"
PLUGIN_ENTRY_POINT_GROUP: Final[str] = "aihw_bench.plugins"
PLUGIN_DOC: Final[str] = "docs/developer-guide/plugin-development.md"
ProviderMap = Mapping[str, object]


class PluginProviderKind(StrEnum):
    """Provider categories accepted by the AIHW-Bench plugin registry."""

    HARDWARE = "hardware"
    MODELS = "models"
    REPORTS = "reports"
    VISUALIZATIONS = "visualizations"
    METRICS = "metrics"
    CLI_COMMANDS = "cli_commands"
    EXPORTERS = "exporters"


SUPPORTED_PROVIDER_KINDS: Final[frozenset[str]] = frozenset(
    provider.value for provider in PluginProviderKind
)


class PluginLifecycleState(StrEnum):
    """Lifecycle state tracked for each discovered plugin."""

    DISCOVERED = "discovered"
    DISABLED = "disabled"
    VALIDATED = "validated"
    REGISTERED = "registered"
    ACTIVE = "active"
    FAILED = "failed"


class PluginManifest(BaseModel):
    """Validated plugin manifest returned by simple plugin packages."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    api_version: str = CORE_PLUGIN_API_VERSION
    package: str = Field(min_length=1)
    description: str = Field(min_length=1)
    providers: tuple[PluginProviderKind, ...] = Field(default_factory=tuple)
    dependencies: tuple[str, ...] = Field(default_factory=tuple)
    capabilities: dict[str, Any] = Field(default_factory=dict)

    @field_validator("dependencies")
    @classmethod
    def reject_self_dependency(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Normalize dependency names and reject blanks."""
        if any(not dependency.strip() for dependency in value):
            raise ValueError("plugin dependencies must not be blank")
        return tuple(dict.fromkeys(dependency.strip() for dependency in value))

    def to_metadata(self) -> PluginMetadata:
        """Convert the manifest to the domain plugin metadata model."""
        return PluginMetadata(
            name=self.name,
            version=self.version,
            api_version=self.api_version,
            package=self.package,
            description=self.description,
            providers=[provider.value for provider in self.providers],
            dependencies=list(self.dependencies),
            capabilities=self.capabilities,
        )


@dataclass(frozen=True, slots=True)
class PluginContext:
    """Context passed to plugin lifecycle callbacks."""

    configuration: Configuration
    logger: logging.Logger


@dataclass(slots=True)
class PluginRegistration:
    """Registration payload returned by an AIHW-Bench plugin entry point."""

    metadata: PluginMetadata
    providers: Mapping[str, ProviderMap] = field(default_factory=dict)
    validate: Callable[[PluginContext], None] | None = None
    activate: Callable[[PluginContext], None] | None = None
    deactivate: Callable[[PluginContext], None] | None = None

    @classmethod
    def from_manifest(
        cls,
        manifest: PluginManifest,
        *,
        providers: Mapping[str | PluginProviderKind, ProviderMap] | None = None,
        validate: Callable[[PluginContext], None] | None = None,
        activate: Callable[[PluginContext], None] | None = None,
        deactivate: Callable[[PluginContext], None] | None = None,
    ) -> Self:
        """Create a registration from a manifest and optional provider objects."""
        normalized_providers = {
            _provider_kind_value(kind): provider_map
            for kind, provider_map in (providers or {}).items()
        }
        return cls(
            metadata=manifest.to_metadata(),
            providers=normalized_providers,
            validate=validate,
            activate=activate,
            deactivate=deactivate,
        )


class PluginRegistry:
    """Validate plugins and expose registered providers by category."""

    def __init__(
        self,
        *,
        configuration: Configuration | None = None,
        core_api_version: str = CORE_PLUGIN_API_VERSION,
        logger: logging.Logger | None = None,
    ) -> None:
        self.configuration = configuration or Configuration()
        self.core_api_version = core_api_version
        self.logger = logger or logging.getLogger(__name__)
        self.metadata: dict[str, PluginMetadata] = {}
        self.states: dict[str, PluginLifecycleState] = {}
        self.providers: dict[str, dict[str, object]] = {
            provider.value: {} for provider in PluginProviderKind
        }
        self.diagnostics: list[Diagnostic] = []
        self._registrations: dict[str, PluginRegistration] = {}

    def register(self, registration: PluginRegistration) -> None:
        """Validate and register one plugin registration."""
        plugin_name = registration.metadata.name
        self.states[plugin_name] = PluginLifecycleState.DISCOVERED
        if self._is_disabled(plugin_name):
            self._record_disabled(registration.metadata)
            return

        try:
            self._validate_registration(registration)
            self._store_registration(registration)
        except Exception as exc:
            self._handle_failure(registration.metadata, "registration", exc)

    def register_many(self, registrations: Sequence[PluginRegistration]) -> None:
        """Register plugins after resolving same-process plugin dependencies."""
        pending = list(registrations)
        while pending:
            ready = [
                registration
                for registration in pending
                if self._dependencies_satisfied(registration)
            ]
            if ready:
                for registration in ready:
                    self.register(registration)
                ready_ids = {id(registration) for registration in ready}
                pending = [
                    registration for registration in pending if id(registration) not in ready_ids
                ]
                continue
            for registration in pending:
                missing = self._missing_dependencies(registration)
                self._handle_failure(
                    registration.metadata,
                    "dependency_resolution",
                    PluginError(
                        "Plugin dependencies are not available.",
                        cause=(
                            f"{registration.metadata.name} requires "
                            f"{', '.join(missing) or 'unresolved plugin dependencies'}."
                        ),
                        suggestion="Install and enable the required AIHW-Bench plugins.",
                        documentation=PLUGIN_DOC,
                    ),
                )
            return

    def activate_all(self, context: PluginContext | None = None) -> None:
        """Run validation and activation callbacks for registered plugins."""
        plugin_context = context or self._context()
        for plugin_name, registration in tuple(self._registrations.items()):
            if self.states.get(plugin_name) is not PluginLifecycleState.REGISTERED:
                continue
            try:
                if registration.validate is not None:
                    registration.validate(plugin_context)
                self.states[plugin_name] = PluginLifecycleState.VALIDATED
                if registration.activate is not None:
                    registration.activate(plugin_context)
                self.states[plugin_name] = PluginLifecycleState.ACTIVE
                self.metadata[plugin_name] = registration.metadata.model_copy(
                    update={"status": "active"}
                )
            except Exception as exc:
                self._handle_failure(registration.metadata, "activation", exc)

    def deactivate_all(self, context: PluginContext | None = None) -> None:
        """Run deactivation callbacks for active plugins in reverse registration order."""
        plugin_context = context or self._context()
        for plugin_name, registration in reversed(tuple(self._registrations.items())):
            if self.states.get(plugin_name) is not PluginLifecycleState.ACTIVE:
                continue
            try:
                if registration.deactivate is not None:
                    registration.deactivate(plugin_context)
                self.states[plugin_name] = PluginLifecycleState.REGISTERED
                self.metadata[plugin_name] = registration.metadata.model_copy(
                    update={"status": "available"}
                )
            except Exception as exc:
                self._handle_failure(registration.metadata, "deactivation", exc)

    def providers_for(self, kind: str | PluginProviderKind) -> dict[str, object]:
        """Return registered providers for a provider category."""
        provider_kind = _provider_kind_value(kind)
        self._validate_provider_kind(provider_kind)
        return dict(self.providers[provider_kind])

    def provider(self, kind: str | PluginProviderKind, name: str) -> object:
        """Return one registered provider by category and provider name."""
        provider_kind = _provider_kind_value(kind)
        self._validate_provider_kind(provider_kind)
        try:
            return self.providers[provider_kind][name]
        except KeyError as exc:
            raise PluginError(
                "Plugin provider is not registered.",
                cause=f"No {provider_kind} provider named {name} is available.",
                suggestion="Check installed plugins and provider names.",
                documentation=PLUGIN_DOC,
            ) from exc

    def plugin_metadata(self) -> list[PluginMetadata]:
        """Return plugin metadata in deterministic order."""
        return [self.metadata[name] for name in sorted(self.metadata)]

    def _validate_registration(self, registration: PluginRegistration) -> None:
        plugin = registration.metadata
        if not plugin.is_compatible(self.core_api_version):
            raise PluginError(
                "Plugin API version is incompatible.",
                cause=(
                    f"{plugin.name} targets plugin API {plugin.api_version}; "
                    f"core supports {self.core_api_version}."
                ),
                suggestion="Install a plugin release compatible with this AIHW-Bench version.",
                documentation=PLUGIN_DOC,
            )
        if plugin.name in self._registrations:
            raise PluginError(
                "Plugin name is already registered.",
                cause=f"Multiple plugins declared the name {plugin.name}.",
                suggestion="Keep one installed distribution for each plugin name.",
                documentation=PLUGIN_DOC,
            )
        declared_provider_kinds = set(plugin.providers)
        for provider_kind in declared_provider_kinds:
            self._validate_provider_kind(provider_kind)
        for provider_kind, provider_map in registration.providers.items():
            self._validate_provider_kind(provider_kind)
            if provider_kind not in declared_provider_kinds:
                raise PluginError(
                    "Plugin provider is not declared in metadata.",
                    cause=f"{plugin.name} registered {provider_kind} without declaring it.",
                    suggestion="Add the provider kind to the plugin manifest.",
                    documentation=PLUGIN_DOC,
                )
            duplicate_names = sorted(set(provider_map) & set(self.providers[provider_kind]))
            if duplicate_names:
                raise PluginError(
                    "Plugin provider name is already registered.",
                    cause=(
                        f"{plugin.name} attempted to register duplicate "
                        f"{provider_kind} provider(s): {', '.join(duplicate_names)}."
                    ),
                    suggestion="Rename the provider or disable the conflicting plugin.",
                    documentation=PLUGIN_DOC,
                )
        missing = self._missing_dependencies(registration)
        if missing:
            raise PluginError(
                "Plugin dependencies are not available.",
                cause=f"{plugin.name} requires {', '.join(missing)}.",
                suggestion="Install and enable the required AIHW-Bench plugins.",
                documentation=PLUGIN_DOC,
            )

    def _store_registration(self, registration: PluginRegistration) -> None:
        plugin = registration.metadata
        for provider_kind, provider_map in registration.providers.items():
            self.providers[provider_kind].update(provider_map)
        self._registrations[plugin.name] = registration
        self.states[plugin.name] = PluginLifecycleState.REGISTERED
        self.metadata[plugin.name] = plugin.model_copy(update={"status": "available"})
        self.logger.info("registered plugin %s", plugin.name)

    def _record_disabled(self, plugin: PluginMetadata) -> None:
        self.states[plugin.name] = PluginLifecycleState.DISABLED
        self.metadata[plugin.name] = plugin.model_copy(update={"status": "disabled"})
        self.logger.info("plugin %s is disabled by configuration", plugin.name)

    def _dependencies_satisfied(self, registration: PluginRegistration) -> bool:
        return not self._missing_dependencies(registration)

    def _missing_dependencies(self, registration: PluginRegistration) -> list[str]:
        missing: list[str] = []
        for dependency in registration.metadata.dependencies:
            state = self.states.get(dependency)
            if state not in {
                PluginLifecycleState.REGISTERED,
                PluginLifecycleState.VALIDATED,
                PluginLifecycleState.ACTIVE,
            }:
                missing.append(dependency)
        return missing

    def _is_disabled(self, plugin_name: str) -> bool:
        enabled = set(self.configuration.plugins.enabled)
        disabled = set(self.configuration.plugins.disabled)
        if plugin_name in disabled:
            return True
        return bool(enabled) and plugin_name not in enabled

    def _handle_failure(self, plugin: PluginMetadata, stage: str, exc: Exception) -> None:
        diagnostic = _diagnostic(plugin.name, stage, exc)
        self.diagnostics.append(diagnostic)
        self.states[plugin.name] = PluginLifecycleState.FAILED
        self.metadata[plugin.name] = plugin.model_copy(
            update={"status": "failed", "diagnostics": [*plugin.diagnostics, diagnostic]}
        )
        self.logger.warning("plugin %s failed during %s: %s", plugin.name, stage, exc)
        if self.configuration.plugins.strict:
            raise PluginError(
                "Plugin failed in strict mode.",
                cause=f"{plugin.name} failed during {stage}: {exc}",
                suggestion=(
                    "Disable the plugin, install compatible dependencies, or turn off strict mode."
                ),
                documentation=PLUGIN_DOC,
            ) from exc

    def _validate_provider_kind(self, provider_kind: str) -> None:
        if provider_kind not in SUPPORTED_PROVIDER_KINDS:
            supported = ", ".join(sorted(SUPPORTED_PROVIDER_KINDS))
            raise PluginError(
                "Plugin provider kind is not supported.",
                cause=f"{provider_kind} is not one of {supported}.",
                suggestion="Use a supported provider kind in the plugin manifest.",
                documentation=PLUGIN_DOC,
            )

    def _context(self) -> PluginContext:
        return PluginContext(configuration=self.configuration, logger=self.logger)


class PluginDiscovery:
    """Discover and normalize plugin registrations from Python entry points."""

    def __init__(
        self,
        *,
        group: str = PLUGIN_ENTRY_POINT_GROUP,
        logger: logging.Logger | None = None,
        strict: bool = False,
    ) -> None:
        self.group = group
        self.logger = logger or logging.getLogger(__name__)
        self.strict = strict
        self.diagnostics: list[Diagnostic] = []

    def discover_entry_points(self) -> list[PluginRegistration]:
        """Load plugin registrations from installed package entry points."""
        registrations: list[PluginRegistration] = []
        for entry_point in metadata.entry_points(group=self.group):
            try:
                registrations.append(self.registration_from_object(entry_point.load()))
            except Exception as exc:
                self._handle_discovery_failure(entry_point.name, exc)
        return registrations

    def discover_objects(self, objects: Iterable[object]) -> list[PluginRegistration]:
        """Normalize in-memory plugin objects for tests and embedded composition roots."""
        registrations: list[PluginRegistration] = []
        for plugin_object in objects:
            try:
                registrations.append(self.registration_from_object(plugin_object))
            except Exception as exc:
                self._handle_discovery_failure(plugin_object.__class__.__name__, exc)
        return registrations

    def registration_from_object(self, plugin_object: object) -> PluginRegistration:
        """Normalize a plugin object, factory, manifest, or registrar into a registration."""
        loaded = plugin_object
        if isinstance(loaded, PluginRegistration):
            return loaded
        if isinstance(loaded, PluginManifest):
            return PluginRegistration.from_manifest(loaded)
        if hasattr(loaded, "register_plugin"):
            registrar = loaded.register_plugin
            if not callable(registrar):
                raise PluginError(
                    "Plugin registrar is not callable.",
                    cause="The register_plugin attribute exists but cannot be called.",
                    suggestion="Expose a register_plugin() function or PluginRegistration object.",
                    documentation=PLUGIN_DOC,
                )
            loaded = registrar()
        elif callable(loaded):
            loaded = loaded()

        if isinstance(loaded, PluginRegistration):
            return loaded
        if isinstance(loaded, PluginManifest):
            return PluginRegistration.from_manifest(loaded)
        raise PluginError(
            "Plugin entry point returned an unsupported object.",
            cause=f"Expected PluginRegistration or PluginManifest, got {type(loaded).__name__}.",
            suggestion="Return PluginRegistration from the aihw_bench.plugins entry point.",
            documentation=PLUGIN_DOC,
        )

    def _handle_discovery_failure(self, plugin_name: str, exc: Exception) -> None:
        diagnostic = Diagnostic(
            code="plugin.discovery_failed",
            message=f"Plugin {plugin_name} could not be discovered.",
            severity=DiagnosticSeverity.ERROR,
            cause=str(exc),
            suggestion="Inspect the plugin entry point and installed package dependencies.",
            documentation=PLUGIN_DOC,
            metadata={"plugin": plugin_name},
        )
        self.diagnostics.append(diagnostic)
        self.logger.warning("plugin %s failed during discovery: %s", plugin_name, exc)
        if self.strict:
            raise PluginError(
                "Plugin discovery failed in strict mode.",
                cause=f"{plugin_name} failed during discovery: {exc}",
                suggestion="Fix or uninstall the failing plugin.",
                documentation=PLUGIN_DOC,
            ) from exc


class PluginManager:
    """High-level plugin loader that combines discovery, registry, and lifecycle."""

    def __init__(
        self,
        *,
        configuration: Configuration | None = None,
        discovery: PluginDiscovery | None = None,
        registry: PluginRegistry | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.configuration = configuration or Configuration()
        self.logger = logger or logging.getLogger(__name__)
        self.discovery = discovery or PluginDiscovery(
            logger=self.logger,
            strict=self.configuration.plugins.strict,
        )
        self.registry = registry or PluginRegistry(
            configuration=self.configuration,
            logger=self.logger,
        )

    def load(
        self,
        registrations: Sequence[PluginRegistration] | None = None,
        *,
        activate: bool = True,
    ) -> PluginRegistry:
        """Discover, register, and optionally activate plugins."""
        discovered = (
            list(registrations)
            if registrations is not None
            else self.discovery.discover_entry_points()
        )
        self.registry.register_many(discovered)
        self.registry.diagnostics.extend(self.discovery.diagnostics)
        if activate:
            self.registry.activate_all()
        return self.registry


def _provider_kind_value(kind: str | PluginProviderKind) -> str:
    return kind.value if isinstance(kind, PluginProviderKind) else kind


def _diagnostic(plugin_name: str, stage: str, exc: Exception) -> Diagnostic:
    return Diagnostic(
        code=f"plugin.{stage}_failed",
        message=f"Plugin {plugin_name} failed during {stage}.",
        severity=DiagnosticSeverity.ERROR,
        cause=str(exc),
        suggestion="Review the plugin configuration, dependencies, and compatibility metadata.",
        documentation=PLUGIN_DOC,
        metadata={"plugin": plugin_name, "stage": stage},
    )
