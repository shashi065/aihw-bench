# Troubleshooting

## `aihw-bench` Command Is Not Found

Install the package into the active environment and confirm the environment's scripts directory is on `PATH`.

```bash
python -m pip install -e .
python -m pip show aihw-bench
```

Then run:

```bash
aihw-bench version
```

## Configuration Does Not Match Expectations

Use the config command to see the merged result:

```bash
aihw-bench config --config path/to/config.yaml --output yaml
```

Check for `AIHW_BENCH_` environment variables that override file settings.

## Model Fails To Load

Confirm that the file exists, is a regular file, and uses a supported extension:

- PyTorch: `.pt`, `.pth`, `.ts`, `.torchscript`
- ONNX: `.onnx`
- TensorFlow Lite: `.tflite`

If the error mentions an optional dependency, install the matching extra or runtime package for that model family.

## GPU Backend Is Rejected

Run:

```bash
aihw-bench doctor
```

The GPU backend requires hardware capability data that indicates GPU availability. On CUDA systems, make sure the local Python environment can import `torch` and that `torch.cuda.is_available()` is true.

## Reports Are Not Generated

Reports require finalized sessions. If a session is still `created` or `running`, rerun the benchmark or inspect diagnostics in the stored session file.

Supported report formats are:

- `json`
- `csv`
- `markdown`
- `html`

## Plugin Fails To Load

Use `aihw-bench doctor` to inspect plugin diagnostics. Common causes are:

- Plugin API version mismatch.
- Missing plugin dependency.
- Unsupported provider kind.
- Entry point does not return `PluginRegistration` or `PluginManifest`.
- Lifecycle callback raises an exception.

Set `plugins.strict: true` only when you want plugin errors to fail the command immediately.

## Tests Fail Because Coverage Is Low

The repository enforces at least 95% coverage. Run:

```bash
python -m pytest
```

Open `htmlcov/index.html` to see uncovered lines. Prefer small deterministic tests with fake backends, fake model loaders, and temporary session stores.

## Docker Desktop Is Installed But Docker Build Cannot Pull Images

On Windows, Docker Desktop may be installed even when `docker` or Docker's credential helper is not visible to the shell that VS Code or WSL is using.

For PowerShell, prepend Docker Desktop's CLI directory before building:

```powershell
$env:PATH = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:PATH
docker build -t aihw-bench:local .
docker run --rm aihw-bench:local doctor
```

For WSL-backed VS Code Dev Containers, make Docker Desktop's credential helper visible from WSL:

```bash
mkdir -p ~/.local/bin
ln -sf "/mnt/c/Program Files/Docker/Docker/resources/bin/docker-credential-desktop.exe" \
  ~/.local/bin/docker-credential-desktop.exe
printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> ~/.profile
```

Then reopen the WSL shell or VS Code window and retry the container build.
