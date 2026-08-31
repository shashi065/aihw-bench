# Homebrew Packaging

AIHW-Bench publishes Homebrew formula content as a generated release asset.

The release workflow builds the source distribution, computes its SHA-256 checksum, and writes a version-specific formula to `dist/aihw-bench.rb`. Maintainers can copy that generated formula into the `aihw-bench/tools` tap or automate tap updates in a later release milestone.

The formula validates:

- `aihw-bench version`
- `aihw-bench doctor`
