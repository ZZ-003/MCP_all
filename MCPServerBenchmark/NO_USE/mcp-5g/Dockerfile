# Image to run the MCP server with Streamable HTTP transport so it can be accessed
# over the network (e.g., Kubernetes / OpenShift) without an external proxy.
#
# OpenShift runs containers as a random UID (e.g. 1000930000) in group 0 (root).
# Rules to follow:
#   1. All files the process needs to write must be owned by root GROUP (not root user)
#      and have g+w permission — OpenShift's arbitrary UID is always in group 0.
#   2. Never pre-populate /tmp inside the image with root-owned files; the runtime
#      UID won't be able to write to them.
#   3. Use a non-root USER in the image so the build itself doesn't run as UID 0.

FROM python:3.12-slim AS base

# ── Environment ──────────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # npm/npx cache → writable scratch dir (NOT /tmp/.npm baked at build time)
    NPM_CONFIG_CACHE=/tmp/npm-cache \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    # pip cache
    PIP_NO_CACHE_DIR=1 \
    # Tell Python / other tools $HOME is writable
    HOME=/tmp/home

WORKDIR /app

# ── System deps (minimal) ────────────────────────────────────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── Python deps ──────────────────────────────────────────────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ── App source ───────────────────────────────────────────────────────────────
COPY . .

# ── OpenShift permission fix ──────────────────────────────────────────────────
# OpenShift's arbitrary UID is always in group 0 (root group).
# Ensure /app and all writable dirs are group-0 writable.
RUN chgrp -R 0 /app \
    && chmod -R g=u /app \
    # Pre-create the runtime writable dirs and give group-0 ownership.
    # DO NOT pre-populate /tmp/npm-cache or /tmp/home — let the runtime UID
    # create them fresh so there are no root-owned files to conflict with.
    && mkdir -p /tmp/home /tmp/npm-cache \
    && chgrp -R 0 /tmp/home /tmp/npm-cache \
    && chmod -R g=u /tmp/home /tmp/npm-cache

# ── Drop to non-root user ─────────────────────────────────────────────────────
# Use UID 1000 for local docker runs; OpenShift will override this with its
# own arbitrary UID at runtime (which is fine — it will still be in group 0).
USER 1000

# ── Ports ─────────────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Runtime env ───────────────────────────────────────────────────────────────
# Default to requiring auth for HTTP transport. Provide MCP_HTTP_BEARER_TOKEN
# at runtime (e.g., via Kubernetes Secret or docker -e) to enable connections.
ENV DANGEROUSLY_OMIT_AUTH=false \
    MCP_TRANSPORT=http \
    MCP_HTTP_HOST=0.0.0.0 \
    MCP_HTTP_PORT=8000

# ── Entrypoint ────────────────────────────────────────────────────────────────
CMD ["python", "server.py"]
