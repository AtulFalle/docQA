# Docker and infrastructure standards

## Images

- **Multi-stage**: build deps in a `builder` stage (`uv sync --no-dev --no-editable`), copy only the venv and needed files into a slim runtime stage. No compilers, git or uv in runtime. **[Review]**
- **Non-root**: create a fixed-uid system user and `USER app`. **[Enforced: hadolint DL3002; Review]**
- **Pinned tags** on every `FROM`; prefer `python:3.12-slim-bookworm` with a version tag, and a digest for production. No `latest` in anything we deploy. **[Enforced: hadolint DL3006/DL3007]**
- **HEALTHCHECK** defined in every service image (see `services/ai-api/Dockerfile`); compose services use `healthcheck` and `depends_on: condition: service_healthy`. **[Review]**
- **One process per container**: AI service, worker, backend are separate containers/commands. No supervisord, no cron inside.
- `PYTHONUNBUFFERED=1`, `EXPOSE` only the real port, exec-form `CMD ["..."]` so signals reach the process (graceful shutdown). **[Enforced: hadolint DL3025]**
- No secrets in the image or build args; no `.env` copied. Config via environment at runtime (`DOCQA_*`).

```dockerfile
# bad
FROM python:latest
COPY . .
RUN pip install -r requirements.txt
CMD python main.py
# good
FROM python:3.12-slim-bookworm
RUN useradd --system --uid 10001 app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
USER app
HEALTHCHECK CMD ["python", "-c", "..."]
CMD ["uvicorn", "docqa_ai_api.main:app", "--host", "0.0.0.0"]
```

## Build hygiene

- `.dockerignore` excludes `.git`, `.venv`, caches, `.env*`, tests data, docs, `node_modules`. Keep the build context small. **[Review]**
- Order layers for caching: dependency manifests before source. Use BuildKit cache mounts for uv where useful.
- Images are rebuilt on base-image updates (Dependabot docker ecosystem) and scanned with Trivy (HIGH/CRITICAL with a fix fail the build). **[Enforced: Trivy]**
- Tag images with git SHA and, for releases, the semantic version. Never overwrite a release tag.

## hadolint rules we care about

Run `hadolint` on every Dockerfile. Treat these as errors: DL3002 (last USER not root), DL3006/DL3007 (tag pinned, not latest), DL3008/DL3013 (pin or avoid OS/pip installs), DL3025 (JSON-form CMD), DL3045 (COPY with WORKDIR), DL4006 (set pipefail). Ignores need a comment with a reason in `.hadolint.yaml`. **[Enforced: hadolint]**

## Compose and local infra

- `infra/docker/docker-compose.yml` is for local development only; credentials in it (`rustfsadmin`, `docqa/docqa`) are local-only defaults and must never be reused elsewhere.
- Pin versions of postgres, redis, qdrant, temporal, otel-lgtm to the minor version used in CI/production so behaviour matches.
- Validate in CI: `docker compose config -q`. **[Enforced: CI `docker` job]**
- Volumes for stateful services; `down -v` wipes data (document it).
- Production infra (hosting, secrets, networking) is decided in ADR 0002; this doc applies once chosen: least-privilege IAM, private networking for data stores, TLS everywhere, backups with tested restores.

## Runtime expectations

- Graceful shutdown on SIGTERM (finish in-flight requests, drain Temporal worker).
- Resource requests/limits set; readiness separate from liveness (`/readyz` vs `/healthz`).
- Logs to stdout as JSON; no log files in containers.
