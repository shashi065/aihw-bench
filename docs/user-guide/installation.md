# Installation

AI Hardware Benchmark Suite targets Python 3.12+.

For repository development, install from a local checkout:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

Package-manager installation targets:

```bash
pip install aihw-bench
uv add aihw-bench
```

Conda-Forge installation target:

```bash
conda install -c conda-forge aihw-bench
```

Docker usage target:

```bash
docker pull ghcr.io/shashi065/aihw-bench:latest
docker run --rm ghcr.io/shashi065/aihw-bench:latest version
```

Build and smoke-test the local image from a checkout:

```bash
docker build -t aihw-bench:local .
docker run --rm aihw-bench:local version
docker run --rm aihw-bench:local doctor
```

The image entrypoint is `aihw-bench`, so command arguments are passed directly after the image name.

Homebrew usage target:

```bash
brew tap aihw-bench/tools
brew install aihw-bench
```

Optional runtime extras will keep heavy framework dependencies out of the core installation:

```bash
pip install "aihw-bench[pytorch]"
pip install "aihw-bench[onnx]"
```
