# syntax=docker/dockerfile:1
#
# Two-stage build:
#   1. "builder" — installs Python deps into a venv using build tools that
#      aren't needed at runtime, and pre-downloads the sentence-transformers
#      embedding model so the running container never needs outbound network
#      access just to answer its first question.
#   2. "runtime" — slim image containing only the venv, the pre-downloaded
#      model cache, and the app source. No compilers, no pip cache, no build
#      tools left behind.
#
# backend/data/ (raw uploads, per-user FAISS indexes, BM25 pickles) and the
# default SQLite file are deliberately NOT part of either stage — see
# .dockerignore. This directory exists in the image only as an empty mount
# point; docker-compose.yml binds a named volume over it at runtime so data
# survives container restarts/rebuilds instead of living in a throwaway
# container layer.

############################
# Stage 1: builder
############################
FROM python:3.11-slim AS builder

# build-essential/gcc: fallback for any dependency that doesn't ship a
# prebuilt wheel for this exact image's platform/Python combination (e.g.
# cryptography, tokenizers on less common architectures like linux/arm64).
# Most of this project's heavier deps (faiss-cpu, torch via
# sentence-transformers, pandas) do ship manylinux wheels, so this mostly
# won't be exercised on linux/amd64 -- it's here so the build doesn't fail
# outright on a platform where one of them doesn't.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model (ingestion/embeddings.py:
# sentence-transformers/all-MiniLM-L6-v2) at build time. Without this, the
# FIRST document upload or chat question against a freshly deployed
# container triggers a Hugging Face Hub download on the request path --
# slow at best, and an outright failure on a host with restricted egress.
# HF_HOME pins the cache location so stage 2 can copy it verbatim.
ENV HF_HOME=/opt/hf_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

############################
# Stage 2: runtime
############################
FROM python:3.11-slim AS runtime

# libgomp1: faiss-cpu links against OpenMP at *runtime*, not just build time
# -- omitting this makes `import faiss` fail with a missing shared-library
# error even though the wheel installed fine in the builder stage.
# ca-certificates: this process makes outbound HTTPS calls at runtime (Groq
# API for every LLM call; Hugging Face Hub as a fallback if HF_HOME's
# pre-baked cache is ever missing/incomplete) -- explicit rather than
# assumed-present, since not every python:*-slim variant ships it.
# curl: used by the Docker/Compose healthcheck below.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser

ENV PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/opt/hf_cache \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/hf_cache /opt/hf_cache

WORKDIR /app
COPY . .

# Empty mount point for the named volume docker-compose.yml attaches at
# /app/data — see this file's top-of-file note and ingestion/vector_store.py
# / ingestion/keyword_store.py / api/documents_routes.py, which create their
# own subdirectories under here on demand (data/raw/{user_id}/,
# data/vector_index/{user_id}/) so nothing further needs pre-creating.
RUN mkdir -p /app/data && chown -R appuser:appuser /app /opt/hf_cache

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# No --reload (that's a dev-only uvicorn flag: it watches the filesystem for
# source changes, which is both wasted overhead and pointless in an
# immutable container image built from a fixed source snapshot).
#
# Shell-form CMD (not exec-form) so ${PORT} is expanded by the shell at
# container start: Render assigns the listen port dynamically via $PORT, and
# an exec-form array would pass the literal string "${PORT}" straight to
# uvicorn instead of expanding it. Falls back to 8000 when PORT is unset
# (local `docker run`, docker-compose). Single worker deliberately (no
# --workers): the per-user FAISS index has no concurrency locking, so
# multiple workers could race and corrupt it — see docs/14-DEPLOYMENT.md
# and PROJECT-AUDIT §14.3.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
