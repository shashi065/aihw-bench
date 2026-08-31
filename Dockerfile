FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m venv /opt/aihw-bench \
    && /opt/aihw-bench/bin/python -m pip install --no-cache-dir --upgrade pip build \
    && /opt/aihw-bench/bin/python -m build --wheel --outdir /dist \
    && /opt/aihw-bench/bin/python -m pip install --no-cache-dir /dist/*.whl \
    && /opt/aihw-bench/bin/aihw-bench version

FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="AIHW-Bench" \
      org.opencontainers.image.description="Universal benchmarking and profiling for AI hardware and accelerators" \
      org.opencontainers.image.source="https://github.com/aihw-bench/aihw-bench" \
      org.opencontainers.image.licenses="Apache-2.0"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/aihw-bench/bin:${PATH}"

COPY --from=builder /opt/aihw-bench /opt/aihw-bench

RUN useradd --create-home --shell /usr/sbin/nologin aihw \
    && aihw-bench version

USER aihw
WORKDIR /workspace

ENTRYPOINT ["aihw-bench"]
CMD ["--help"]
