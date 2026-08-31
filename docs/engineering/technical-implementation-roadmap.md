# Technical Implementation Roadmap

Document status: Official execution plan  
Scope: Milestones required to move AIHW-Bench from foundation to production-ready `v1.0.0`  
Constraint: Each milestone must leave the repository stable and releasable

## Roadmap Principles

- Every milestone produces a working, documented, tested repository state.
- Public surfaces are introduced only when their contracts are documented.
- Optional heavy dependencies remain isolated behind extras or plugins.
- Release readiness is built continuously, not deferred to `v1.0.0`.
- Architecture, SRS, SDD, PRD, and Engineering Handbook are mandatory inputs for planning.

## Milestone 0: Repository Foundation

### Objectives

Establish the professional open-source foundation required for all future work.

### Scope

Repository structure, packaging metadata, documentation baseline, governance files, CI/CD foundation, issue and pull request templates, development environment, release strategy, and contributor standards.

### Deliverables

- Repository structure.
- Python packaging with PEP 517, PEP 518, and PEP 621 metadata.
- Poetry-compatible configuration.
- README.
- License.
- Changelog.
- Contribution guide.
- Code of conduct.
- Security policy.
- Roadmap.
- Project constitution.
- PRD, SRS, SDD, architecture docs, and engineering handbook.
- GitHub issue templates.
- Pull request template.
- CI foundation for formatting, linting, typing, tests, docs, and package build.
- Development container.

### Engineering Tasks

- Define package identity and metadata.
- Create documentation site structure.
- Add governance files.
- Add GitHub workflow skeletons.
- Add release workflow skeleton.
- Define contributor standards.
- Define quality gates.

### Expected Repository Changes

- Root metadata files.
- `.github` workflows and templates.
- `docs` hierarchy.
- `src` package root.
- `tests` root.
- `packaging` root.
- `.devcontainer`.

### Dependencies

None.

### Estimated Difficulty

Medium. The work is broad but not technically deep.

### Acceptance Criteria

- Documentation builds in strict mode.
- Package metadata parses.
- Repository has governance and contribution templates.
- CI workflow definitions exist.
- Release strategy is documented.

### Definition of Done

- All foundation documents are present and linked.
- No generated files are committed unintentionally.
- Repository is ready for domain and infrastructure implementation.

### Potential Risks

- Over-documentation without implementation discipline.
- Premature public API commitments.
- Incomplete release credentials.

### Future Improvements

- Versioned documentation.
- Contributor onboarding automation.
- Repository health dashboard.

## Milestone 1: Core Infrastructure

### Objectives

Implement the stable domain and infrastructure foundation used by all later subsystems.

### Scope

Logging, configuration, exceptions, utilities, session management, data models, validation, dependency management, and core interfaces.

### Deliverables

- Domain data models.
- Domain port interfaces.
- Error hierarchy.
- Configuration resolver.
- Filesystem session store.
- Logging and diagnostics framework.
- Safe path utilities.
- Serialization utilities.
- Validation helpers.
- Dependency groups and extras baseline.

### Engineering Tasks

- Implement `BenchmarkSession`, `BenchmarkResult`, `Metric`, `HardwareProfile`, `ModelMetadata`, `PluginMetadata`, `Configuration`, and `ExportArtifact` models.
- Implement typed exception classes.
- Implement configuration source precedence.
- Implement YAML and JSON config loading.
- Implement environment variable parsing.
- Implement session directory layout.
- Implement atomic writes for canonical session artifacts.
- Implement structured diagnostics.

### Expected Repository Changes

- Domain package modules.
- Application command/result models.
- Infrastructure configuration and storage modules.
- Unit tests for data models, validation, and configuration.
- Developer documentation for configuration and sessions.

### Dependencies

Milestone 0.

### Estimated Difficulty

High. This milestone defines foundational contracts.

### Acceptance Criteria

- Core domain models are serializable and validated.
- Configuration precedence is deterministic.
- Session store persists and loads immutable sessions.
- Errors are classified and documented.
- Unit and integration tests cover normal and failure paths.

### Definition of Done

- Public model and configuration APIs are documented.
- CI quality gates pass.
- Session schema is versioned.
- No benchmark execution features depend on undefined models.

### Potential Risks

- Data models becoming too broad.
- Configuration complexity growing too early.
- Schema changes after persistence begins.

### Future Improvements

- Schema migration helpers.
- SQLite session store.
- Secret reference support.

## Milestone 2: Benchmark Engine

### Objectives

Implement the canonical benchmark lifecycle with deterministic measurement behavior.

### Scope

Execution engine, timing engine, warmup, measured iterations, statistics, scheduling foundation, lifecycle states, cleanup, and recovery.

### Deliverables

- Benchmark service.
- Lifecycle state machine.
- Timing abstraction.
- Warmup runner.
- Measurement runner.
- Statistics aggregation foundation.
- Fake/reference backend for validation.
- Progress events.
- Failure and partial-session handling.

### Engineering Tasks

- Implement benchmark command/result types.
- Implement lifecycle coordinator.
- Implement monotonic timing abstraction.
- Implement warmup exclusion from primary metrics.
- Implement measured observation capture.
- Implement timeout and retry policy.
- Implement cleanup guarantees.
- Persist partial sessions on recoverable failure.

### Expected Repository Changes

- Application benchmark service modules.
- Domain execution models.
- Fake/reference backend.
- Integration tests for benchmark flow.
- Benchmark lifecycle documentation.

### Dependencies

Milestone 1.

### Estimated Difficulty

High. Measurement correctness and failure handling are central to the product.

### Acceptance Criteria

- A fake/reference backend can run a complete benchmark session.
- Warmup and measurement data are separated.
- Failed runs preserve diagnostics.
- Raw observations are persisted.
- Statistics are deterministic for fixed inputs.

### Definition of Done

- Benchmark lifecycle is documented.
- CLI or API smoke path exists for internal validation.
- Unit, integration, regression, and benchmark validation tests pass.

### Potential Risks

- Framework overhead contaminating measurements.
- State machine complexity.
- Incomplete failure recovery.

### Future Improvements

- Parallel scheduling.
- Distributed execution.
- Hardware lab orchestration.

## Milestone 3: Model Support

### Objectives

Add runtime-aware model/workload support while keeping model metadata independent from specific backends.

### Scope

PyTorch, ONNX Runtime, TensorFlow Lite, model loading, validation, metadata extraction, input specifications, and optional dependency handling.

### Deliverables

- Model metadata extraction contracts.
- Workload model.
- Model loader registry.
- PyTorch model support behind optional extra.
- ONNX Runtime model support behind optional extra.
- TensorFlow Lite support behind optional extra where platform-compatible.
- Missing dependency diagnostics.

### Engineering Tasks

- Implement workload and model metadata interfaces.
- Implement format detection.
- Implement optional dependency guards.
- Implement metadata extraction where available.
- Define input shape and sample input configuration.
- Document supported formats and limitations.

### Expected Repository Changes

- Model layer modules.
- Runtime adapter modules behind extras.
- Optional backend tests.
- Model support documentation.

### Dependencies

Milestones 1 and 2.

### Estimated Difficulty

High due to optional runtimes and platform differences.

### Acceptance Criteria

- Missing optional dependencies fail gracefully.
- Model metadata is captured in sessions.
- Runtime-specific loading does not leak into domain logic.
- At least PyTorch and ONNX Runtime adapters run in optional test environments.

### Definition of Done

- Model APIs are documented.
- Optional dependency installation instructions exist.
- Runtime support is covered by conditional CI or documented local validation.

### Potential Risks

- Heavy dependency footprint.
- Runtime version incompatibility.
- Model metadata inconsistency across frameworks.

### Future Improvements

- Compiler IR workloads.
- Synthetic workload generators.
- Dataset-aware benchmark inputs.

## Milestone 4: Hardware Backend Layer

### Objectives

Provide hardware abstraction and initial backend coverage for CPU, GPU, and simulator-class targets.

### Scope

CPU backend, GPU backend, RTL simulator backend contract, backend abstraction, hardware detection, device capability discovery, and target metadata.

### Deliverables

- Hardware backend interface.
- CPU backend.
- GPU capability interface.
- Simulator backend contract.
- Hardware inspector.
- Device selector.
- Capability validation.

### Engineering Tasks

- Implement host hardware inspection.
- Implement CPU backend.
- Define GPU backend interface and optional provider path.
- Define RTL simulator backend contract.
- Implement device selection and capability checks.
- Capture hardware metadata in sessions.

### Expected Repository Changes

- Hardware layer modules.
- Backend provider modules.
- Hardware detection docs.
- Backend conformance tests.

### Dependencies

Milestones 1, 2, and 3.

### Estimated Difficulty

High because hardware diversity is large.

### Acceptance Criteria

- CPU backend executes benchmark workloads.
- Hardware metadata is persisted.
- Unsupported devices fail before execution with clear diagnostics.
- Backend conformance tests validate provider behavior.

### Definition of Done

- Backend abstraction is documented.
- CPU backend is stable.
- Simulator and GPU extension contracts are ready for plugin authors.

### Potential Risks

- Overfitting abstractions to early backends.
- Platform-specific hardware detection failures.
- Unclear separation between backend and profiler responsibilities.

### Future Improvements

- ROCm, CUDA, Metal, OpenVINO, FPGA, and remote embedded providers.
- Hardware lab inventory.

## Milestone 5: Metrics Engine

### Objectives

Implement the core metrics engine and result aggregation system.

### Scope

Latency, throughput, memory, CPU usage, GPU usage, FLOPS estimation, arithmetic intensity, result aggregation, unit handling, and assumptions.

### Deliverables

- Metric provider interface.
- Built-in metric providers.
- Unit normalization.
- Aggregation pipeline.
- Missing metric diagnostics.
- Regression threshold foundation.

### Engineering Tasks

- Implement latency summaries.
- Implement throughput and FPS metrics.
- Implement memory summaries.
- Implement CPU utilization summaries.
- Implement optional GPU utilization summaries.
- Implement model-size and FLOPS estimates.
- Implement arithmetic intensity estimates.
- Persist metric assumptions.

### Expected Repository Changes

- Metrics engine modules.
- Metric docs and reference tables.
- Golden-data tests.
- Regression tests for metric stability.

### Dependencies

Milestones 1, 2, 3, and 4.

### Estimated Difficulty

Medium to high. Derived metrics require careful assumptions.

### Acceptance Criteria

- Metrics include units, sources, and assumptions.
- Missing data is explicit.
- Aggregation is deterministic.
- Golden-data tests pass.

### Definition of Done

- Metrics reference documentation exists.
- Metric provider API is stable enough for plugin work.
- Reports can consume metric outputs without ad hoc conversion.

### Potential Risks

- Misleading derived metrics.
- Unit conversion mistakes.
- Inconsistent metric names across backends.

### Future Improvements

- Confidence intervals.
- Energy efficiency.
- Statistical significance testing.

## Milestone 6: Reporting

### Objectives

Generate professional benchmark artifacts for users, automation, and release workflows.

### Scope

HTML, CSV, JSON, Markdown, report view models, artifact manifests, recommendations, and report generation policies.

### Deliverables

- Report provider interface.
- JSON reporter.
- CSV exporter.
- Markdown reporter.
- HTML reporter.
- Report view model.
- Artifact manifest.
- Recommendation policy foundation.

### Engineering Tasks

- Build report data model from sessions.
- Implement JSON and CSV structured outputs.
- Implement Markdown summaries.
- Implement HTML reports with tables and defined chart integration sections.
- Compute artifact checksums.
- Document report formats.

### Expected Repository Changes

- Reporting modules.
- Report templates.
- Snapshot tests.
- Report documentation and examples.

### Dependencies

Milestones 1, 2, and 5.

### Estimated Difficulty

Medium.

### Acceptance Criteria

- Reports include summary, configuration, hardware, metrics, diagnostics, and artifact manifest.
- JSON and CSV preserve units and provenance.
- Report generation does not mutate session data.
- Snapshot tests validate stable output.

### Definition of Done

- All essential report formats are documented.
- Report outputs are usable in CI and human review.
- Errors are classified and recoverable.

### Potential Risks

- Report templates coupling to internal models.
- HTML complexity growing before visualization stabilizes.

### Future Improvements

- PDF reports.
- Static dashboard bundles.
- Hosted report publishing.

## Milestone 7: Visualization

### Objectives

Add charting and dashboard foundation for benchmark analysis.

### Scope

Interactive charts, timeline, roofline, comparisons, latency distributions, memory graphs, utilization charts, and dashboard foundation.

### Deliverables

- Visualization provider interface.
- Chart specification data model.
- Plotly-based chart providers.
- Timeline charts.
- Roofline charts.
- Comparison charts.
- Dashboard data model foundation.

### Engineering Tasks

- Define chart spec schema.
- Normalize chart data from sessions.
- Implement latency distribution charts.
- Implement memory and utilization charts.
- Implement comparison charts.
- Integrate charts into HTML reports.
- Document chart assumptions.

### Expected Repository Changes

- Visualization modules.
- Chart snapshot tests.
- Visualization documentation.
- Report integration updates.

### Dependencies

Milestones 5 and 6.

### Estimated Difficulty

Medium to high due to chart correctness and data size concerns.

### Acceptance Criteria

- Chart specs are deterministic.
- Missing data is visible.
- Large data is downsampled safely when needed.
- HTML reports include interactive charts.

### Definition of Done

- Visualization provider API is documented.
- Chart families have examples.
- Dashboard foundation does not execute benchmarks directly.

### Potential Risks

- Chart rendering bloat.
- Misleading visualizations.
- Coupling visualizations to report templates.

### Future Improvements

- Live dashboard.
- Multi-session exploration.
- Web-based campaign analysis.

## Milestone 8: CLI

### Objectives

Deliver a professional, discoverable, automation-friendly command line interface.

### Scope

Command structure, autocomplete, progress bars, Rich output, error handling, machine-readable output, and CLI reference.

### Deliverables

- `benchmark` command.
- `profile` command.
- `compare` command.
- `report` command.
- `dashboard` command foundation.
- `export` command.
- `doctor` command.
- `version` command.
- Shell completion support.
- CLI docs.

### Engineering Tasks

- Implement command groups.
- Implement output renderer abstraction.
- Implement JSON output mode.
- Implement progress rendering.
- Map exceptions to exit codes.
- Add shell completion documentation.
- Add CLI tests for each command.

### Expected Repository Changes

- Presentation CLI modules.
- CLI test suite.
- CLI reference docs.
- Shell completion docs.

### Dependencies

Milestones 1 through 7.

### Estimated Difficulty

Medium.

### Acceptance Criteria

- Commands have help, examples, and documented exit codes.
- CLI errors are user-friendly.
- Machine-readable output is stable.
- CLI tests cover success and failure paths.

### Definition of Done

- CLI reference builds.
- Autocomplete instructions are documented.
- CLI can drive the core benchmark/report workflow.

### Potential Risks

- CLI becoming coupled to business logic.
- Rich output interfering with automation.

### Future Improvements

- Plugin-provided commands.
- Interactive setup wizard.
- Local dashboard launcher.

## Milestone 9: Plugin Framework

### Objectives

Enable third parties to extend AIHW-Bench without modifying core code.

### Scope

Plugin discovery, lifecycle, API, validation, provider registry, diagnostics, and conformance tests.

### Deliverables

- Entry-point plugin loader.
- Plugin descriptor schema.
- Provider registry.
- Plugin lifecycle states.
- Plugin validation.
- Plugin diagnostics.
- Example plugin package.
- Plugin development guide.

### Engineering Tasks

- Implement entry point scanning.
- Implement descriptor validation.
- Implement provider registration.
- Implement duplicate detection.
- Implement API version compatibility checks.
- Implement plugin diagnostics in `doctor`.
- Add conformance tests.

### Expected Repository Changes

- Plugin manager modules.
- Example plugin under examples.
- Plugin docs.
- Plugin conformance tests.

### Dependencies

Milestones 1, 5, 6, 7, and 8.

### Estimated Difficulty

High because public extension contracts are long-lived.

### Acceptance Criteria

- Plugins can register backend, metric, reporter, visualizer, exporter, model, hardware, and CLI providers.
- Invalid plugins fail with diagnostics.
- Built-in providers use the same registry model where practical.
- Plugin API is documented.

### Definition of Done

- Example plugin installs and validates.
- Provider contracts are documented and tested.
- API versioning policy is enforced.

### Potential Risks

- Premature plugin API freeze.
- In-process plugin security assumptions.
- Provider naming conflicts.

### Future Improvements

- Signed plugins.
- Out-of-process plugins.
- Plugin marketplace metadata.

## Milestone 10: Testing

### Objectives

Reach comprehensive test coverage and quality confidence across subsystems.

### Scope

Unit tests, integration tests, CLI tests, performance tests, regression tests, coverage reports, compatibility tests, benchmark validation tests.

### Deliverables

- Unit test suite.
- Integration test suite.
- CLI test suite.
- Regression test suite.
- Performance test suite.
- Optional backend test matrix.
- Coverage reporting.
- Test fixtures.

### Engineering Tasks

- Define test markers.
- Add fixtures for sessions, configs, plugins, and model metadata.
- Add benchmark validation tests.
- Add malformed input regression tests.
- Add package install smoke tests.
- Configure coverage thresholds.

### Expected Repository Changes

- Expanded `tests` hierarchy.
- Test fixture docs.
- CI workflow updates.
- Coverage gates.

### Dependencies

Milestones 1 through 9.

### Estimated Difficulty

High due to subsystem breadth and optional environments.

### Acceptance Criteria

- Required test categories exist.
- Coverage target is enforced.
- Optional backend tests are conditional.
- Regression tests exist for known failure modes.

### Definition of Done

- CI test suite is stable.
- Test docs explain local and CI workflows.
- Performance validation is repeatable.

### Potential Risks

- Slow tests discouraging contributors.
- Flaky hardware-dependent tests.
- Coverage masking weak assertions.

### Future Improvements

- Nightly hardware matrix.
- Benchmark corpus.
- Fuzz testing for config/session inputs.

## Milestone 11: Documentation

### Objectives

Deliver complete user, developer, API, CLI, and plugin documentation.

### Scope

MkDocs, API docs, tutorials, examples, architecture docs, developer guide, plugin guide, troubleshooting, performance guide.

### Deliverables

- User guide.
- Developer guide.
- API reference.
- CLI reference.
- Plugin guide.
- Tutorials.
- Examples.
- Troubleshooting guide.
- Performance guide.
- Architecture diagrams.

### Engineering Tasks

- Generate API docs.
- Write CLI reference.
- Create tutorials for benchmark/report/compare/plugin flows.
- Add example configs and outputs.
- Add troubleshooting docs.
- Add performance methodology docs.
- Validate docs in strict mode.

### Expected Repository Changes

- Expanded `docs`.
- Example files.
- Documentation workflow updates.

### Dependencies

Milestones 1 through 10.

### Estimated Difficulty

Medium to high due to breadth.

### Acceptance Criteria

- Public APIs and commands are documented.
- Tutorials follow implemented behavior.
- Examples are validated.
- Docs build in strict mode.

### Definition of Done

- Documentation supports first-time users and plugin authors.
- No broken links.
- Docs are release-ready for GitHub Pages.

### Potential Risks

- Docs drifting from implementation.
- Examples becoming stale.

### Future Improvements

- Versioned docs.
- Tutorial videos.
- Gallery of reports.

## Milestone 12: Release Engineering

### Objectives

Automate professional multi-platform releases.

### Scope

GitHub Actions, GitHub Releases, PyPI, TestPyPI, GitHub Pages, Docker Hub, Conda-Forge preparation, SBOM generation, signed releases, trusted publishing.

### Deliverables

- Tag-driven release workflow.
- Version validation.
- Wheel and source distribution builds.
- SBOM generation.
- Checksums.
- GitHub Release publication.
- PyPI and TestPyPI publishing.
- GitHub Pages deployment.
- Docker image build/push.
- Conda-Forge metadata.
- Homebrew metadata.
- Signed release design.

### Engineering Tasks

- Enforce tag and package version alignment.
- Generate release notes from changelog.
- Build distributions.
- Generate SBOM and checksums.
- Run security scans.
- Verify install on Windows, Linux, and macOS.
- Publish docs and artifacts.
- Document downstream packaging process.

### Expected Repository Changes

- Release workflows.
- Packaging metadata.
- Release documentation.
- Install verification scripts or workflow steps.

### Dependencies

Milestones 0 through 11.

### Estimated Difficulty

High due to registry and ecosystem integration.

### Acceptance Criteria

- A semantic version tag triggers release automation.
- Release artifacts include wheel, sdist, SBOM, checksums, release notes, and docs.
- Installation verifies across supported OSes.
- Publishing uses trusted publishing where supported.

### Definition of Done

- Release dry run succeeds.
- Registry credentials/environments are documented.
- Release process requires no manual packaging.

### Potential Risks

- Registry credential misconfiguration.
- Platform-specific install failures.
- Downstream package manager review delays.

### Future Improvements

- Sigstore provenance.
- Winget, Chocolatey, Snapcraft, AUR, and Nix automation.

## Milestone 13: Version 1.0 Release

### Objectives

Finalize the first stable public release.

### Scope

Final QA, performance validation, security audit, documentation audit, API freeze, release candidate, and `v1.0.0`.

### Deliverables

- API freeze.
- CLI freeze.
- Plugin API freeze.
- Configuration schema freeze.
- Session schema freeze.
- Security audit report.
- Performance validation report.
- Documentation audit.
- Release candidate.
- Stable `v1.0.0` release.

### Engineering Tasks

- Run full CI and optional backend matrices.
- Audit public API docs.
- Audit CLI examples.
- Audit plugin compatibility.
- Audit release artifacts.
- Validate package installation.
- Validate report outputs.
- Validate migration/deprecation docs.
- Cut release candidate.
- Resolve RC blockers.
- Tag `v1.0.0`.

### Expected Repository Changes

- Final changelog.
- Release notes.
- Audit documents.
- Version bump.
- Stable docs.

### Dependencies

Milestones 0 through 12.

### Estimated Difficulty

High due to stabilization and release discipline.

### Acceptance Criteria

- All required CI jobs pass.
- Coverage target is met.
- Docs build and deploy.
- Release candidate has no blocking issues.
- Stable artifacts publish successfully.

### Definition of Done

- `v1.0.0` is tagged and published.
- GitHub Release, PyPI package, docs site, SBOM, checksums, and container image are available.
- Maintainers announce stable API and support policy.

### Potential Risks

- Late API instability.
- Optional backend flakiness.
- Documentation gaps.
- Security audit findings.

### Future Improvements

- `v1.x` maintenance branch.
- `v2.0` planning.
- Plugin certification program.

## Critical Path

The critical path is:

```text
Milestone 0
-> Milestone 1
-> Milestone 2
-> Milestone 5
-> Milestone 6
-> Milestone 8
-> Milestone 9
-> Milestone 10
-> Milestone 11
-> Milestone 12
-> Milestone 13
```

Model support and hardware backends can start after the benchmark engine foundation exists, but stable reporting, CLI, plugin, testing, documentation, and release work depend on the core data and lifecycle contracts.

## Parallel Development Opportunities

- Documentation can proceed alongside every milestone.
- Release engineering can mature in parallel after Milestone 0.
- Metrics and reporting can begin with fake sessions before full hardware support.
- Model support and hardware backend work can run in parallel after Milestone 2.
- CLI command polish can proceed in parallel with reporting once application services are stable.
- Plugin documentation can begin before plugin implementation once provider contracts stabilize.

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| Benchmark measurements include framework overhead | High | Medium | Separate lifecycle phases, validate overhead, keep reporting outside measured regions |
| Plugin API freezes too early | High | Medium | Mark plugin API experimental until conformance tests and examples exist |
| Optional runtime dependencies break installs | High | Medium | Keep extras optional, add missing dependency diagnostics, run conditional tests |
| Hardware-dependent tests become flaky | Medium | High | Separate required and optional matrices, use fake backends for core CI |
| Documentation drifts from implementation | High | Medium | Strict docs build, docs required in PR checklist, examples validated |
| Release credentials fail | Medium | Medium | Use trusted publishing and documented environments |
| Derived metrics are misleading | High | Medium | Store assumptions, document estimates, mark unavailable data explicitly |
| Session schema changes frequently | High | Medium | Version schemas early, add migration design before stable release |
| CLI output becomes hard to automate | Medium | Medium | Maintain machine-readable output modes |
| Project scope expands too quickly | High | High | Milestone gates and maintainer roadmap review |

## Dependency Graph

```text
M0 Repository Foundation
  -> M1 Core Infrastructure
    -> M2 Benchmark Engine
      -> M3 Model Support
      -> M4 Hardware Backend Layer
      -> M5 Metrics Engine
        -> M6 Reporting
          -> M7 Visualization
        -> M8 CLI
        -> M9 Plugin Framework
          -> M10 Testing
            -> M11 Documentation
              -> M12 Release Engineering
                -> M13 Version 1.0 Release
```

Milestone 12 begins earlier in lightweight form but cannot be complete until documentation, tests, and packaging are stable.

## Release Timeline

The timeline is expressed as engineering phases rather than calendar commitments.

| Phase | Milestones | Release Target |
| --- | --- | --- |
| Foundation | M0 | `0.0.x` |
| Core | M1 | `0.1.0` |
| Execution | M2 | `0.2.0` |
| Runtime and Hardware | M3, M4 | `0.3.0` |
| Metrics | M5 | `0.4.0` |
| Reports and Visualization | M6, M7 | `0.5.0` |
| CLI and Plugins | M8, M9 | `0.6.0` |
| Quality and Docs | M10, M11 | `0.7.0` |
| Release Automation | M12 | `0.8.0` or release-candidate track |
| Stabilization | M13 | `1.0.0` |

## Quality Gates

Every milestone must satisfy:

- SRS requirement traceability updated.
- SDD alignment checked.
- Public APIs documented before release.
- User-facing changes added to changelog.
- Tests cover normal and failure paths once implementation begins.
- CI passes.
- Documentation builds in strict mode.
- Package metadata remains valid.
- Security impact reviewed.
- Performance impact reviewed for benchmark-sensitive code.

## Roadmap Governance

Roadmap changes require maintainer review when they affect:

- Public API stability.
- Plugin contracts.
- Persisted data schemas.
- Release process.
- Supported platforms.
- Benchmark methodology.
- Security posture.

Major roadmap changes should be captured in an ADR and linked from this document.
