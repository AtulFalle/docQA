# Build context: repository root.  docker build -f services/ingestion-worker/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY . /app
RUN uv sync --no-dev --package docqa-workers --no-editable

FROM python:3.12-slim-bookworm
RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
CMD ["docqa-worker"]
