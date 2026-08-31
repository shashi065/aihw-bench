# Performance Tests

Performance tests validate framework overhead, benchmark lifecycle costs, metric aggregation speed, report generation time, and large-session behavior.

Performance tests must document measurement method, expected budget, and environment sensitivity before becoming required CI gates.

Required CI performance tests must use deterministic inputs, fake backends, and scripted timing where possible. Hardware, accelerator, or optional-runtime performance baselines belong in optional jobs with explicit markers and documented environment requirements.
