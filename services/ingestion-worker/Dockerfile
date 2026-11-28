# Build context: repository root.  docker build -f services/ingestion-worker/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY . /app
RUN uv sync --no-dev --package docqa-workers --no-editable

FROM python:3.12-slim-bookworm AS runtime
# Pull in Debian security fixes newer than the base image. CI rebuilds this stage without the
# layer cache (no-cache-filters: runtime), so every build gets the current fixes.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
CMD ["docqa-worker"]
