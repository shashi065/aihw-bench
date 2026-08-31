# Security Policy

## Supported Versions

Security fixes are provided for the current stable release line: **2.x**. The supported package version is published in `pyproject.toml` and exposed as `aihw_bench.__version__`.

## Reporting a Vulnerability

Do not report security vulnerabilities through public GitHub issues. Send a private report to the maintainers with the affected version or commit, reproduction steps, impact assessment, and known mitigations.

## Security Scope

Relevant issues include unsafe file handling, plugin execution, unsafe deserialization, command injection, exposed secrets, report/dashboard generation vulnerabilities, database reliability, and dependency supply-chain risks. Plugins execute in-process and are therefore trusted code; do not install plugins from untrusted sources.
