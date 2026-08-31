# Integration Tests

Integration tests validate collaboration between implemented subsystems, such as configuration resolution, benchmark orchestration, session persistence, reporting, exports, and plugin loading.

Integration tests should use temporary directories, deterministic fixtures, and fake providers unless the test is explicitly marked for an optional runtime or hardware environment.
