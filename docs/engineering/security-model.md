# Security Model

## Threat Model

AIHW-Bench processes local files, configuration, plugins, models, reports, and optional runtime integrations. Main risks include path traversal, unsafe deserialization, arbitrary plugin execution, malicious model files, dependency vulnerabilities, accidental secret exposure, and unsafe report output.

## Input Validation

All external inputs are validated at boundaries:

- CLI arguments.
- Configuration files.
- Environment variables.
- Plugin descriptors.
- Model paths.
- Session files.
- Report output paths.

Validation errors include the failing field, cause, and suggested correction.

## Configuration Security

Configuration files are data only. They must not execute code. Unknown keys are rejected in strict mode. Path values are resolved through safe path helpers.

## Safe File Handling

- Reject path traversal.
- Avoid overwriting canonical session files.
- Use atomic writes for canonical artifacts.
- Treat existing session data as immutable.
- Never include secrets in reports by default.

## Plugin Isolation

Initial plugins run in-process, so they are trusted code. The plugin system still validates descriptors and isolates load failures. Future high-risk integrations may support subprocess or remote execution isolation.

## Dependency Security

Release workflows include dependency auditing and SBOM generation. Optional runtime dependencies are isolated behind extras and plugins to reduce the default dependency footprint.

## Report Security

Report renderers escape user-provided values by default. HTML reports avoid executing arbitrary user content. External assets are controlled by report configuration.

## Future Security Work

- Signed plugin metadata.
- Plugin trust policies.
- Report sanitization test suite.
- Supply-chain provenance attestations.
