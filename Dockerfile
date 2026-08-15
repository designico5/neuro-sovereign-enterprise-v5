# syntax=docker/dockerfile:1
# Neuro-Sovereign Enterprise v5 - container image
# Multi-stage build: builder installs deps, runtime ships a slim image.

# ===== Stage 1: builder =====
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build toolchain + headers for C extensions
# (cryptography, pynacl, argon2-cffi, pycryptodome, lxml, Pillow, reportlab, pygit2, paramiko, ...)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ build-essential \
        libffi-dev libssl-dev \
        libxml2-dev libxslt1-dev \
        libjpeg-dev zlib1g-dev \
        pkg-config python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Project metadata first (keeps the dependency-resolution layer cacheable)
COPY pyproject.toml README.md ./
COPY neurosovereign ./neurosovereign

# Editable install pulls in the full runtime dependency tree from pyproject.toml
RUN python -m pip install --upgrade pip && pip install -e . --no-cache

# ===== Stage 2: runtime =====
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NSE_DATA_DIR=/app/state

WORKDIR /app

# Runtime shared libraries required by the compiled wheels copied from builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        libffi8 libssl3 \
        libxml2 libxslt1.1 \
        libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Non-root user (uid 1000)
RUN groupadd --gid 1000 nse \
 && useradd  --uid 1000 --gid nse --create-home --shell /bin/bash nse

# Installed site-packages from builder (deps + editable-install finder)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Application source at the same /app path so the editable install resolves
COPY neurosovereign ./neurosovereign

# Persistent state directory, owned by the non-root user
RUN mkdir -p /app/state && chown -R 1000:1000 /app

USER 1000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=3 \
  CMD ["python", "-m", "neurosovereign.cli", "status"]

CMD ["python", "-m", "neurosovereign.cli", "start"]
