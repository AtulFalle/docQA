# Build context: repository root.  docker build -f services/ai-api/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY . /app
RUN uv sync --no-dev --package docqa-ai-api --no-editable

FROM python:3.12-slim-bookworm
RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"]
CMD ["uvicorn", "docqa_ai_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
