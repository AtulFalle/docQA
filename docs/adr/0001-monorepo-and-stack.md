# 0001. Monorepo layout and core stack

> Superseded in part by ADR 0005

- Status: Accepted
- Date: 2026-11-24

## Context

docQA is a production RAG / QA system over large document volumes with per-document access control. It needs an ingestion pipeline (extract, chunk, embed, index), a query API, and an evaluation harness, and the parts must share one data model and one set of tests. The architecture plan (`architecture/production-rag-plan-v1.md` in the project) sets the component choices this ADR records.

## Decision

Use a single repository managed as a **uv workspace** with these packages:

| Dist name       | Import name     | Path               | Role                                   |
|-----------------|-----------------|--------------------|----------------------------------------|
| docqa-core      | docqa_core      | `libs/core/`       | Settings, logging, telemetry, DB models, migrations support |
| docqa-api       | docqa_api       | `api/`             | FastAPI HTTP service                   |
| docqa-workers   | docqa_workers   | `workers/`         | Temporal workflows and activities      |
| docqa-eval      | docqa_eval      | `eval/`            | Golden dataset tooling and metrics (standalone, pydantic only) |

Stack:

- **Language:** Python 3.12, type-hinted, checked with mypy (strict).
- **API:** FastAPI on uvicorn.
- **Relational store:** PostgreSQL 16, accessed with SQLAlchemy 2.0 (async) and psycopg 3. Migrations use Alembic. Tenant isolation uses Postgres row-level security with `app.tenant_id` set per transaction.
- **Vector index:** Qdrant.
- **Workflow orchestration:** Temporal for ingestion.
- **Cache / rate limiting:** Redis.
- **Object storage:** RustFS (Apache-2.0, S3-compatible) locally, S3-compatible elsewhere. Replaced MinIO, which is no longer distributed as free open-source images.
- **Observability:** OpenTelemetry, exported to Grafana LGTM (Tempo, Loki, Prometheus, Grafana). Structured JSON logs through structlog.
- **LLM tracing and prompt analytics:** Langfuse.
- **Build and packaging:** hatchling per package, uv for dependencies, Docker images per deployable service.

Dependencies are pinned by lower bound in each `pyproject.toml`. `uv.lock` will be committed once the dependency set settles (M0 follow-up).

## Consequences

- One `uv sync --all-packages` gives a working environment for every package. Cross-package changes land in one PR and one CI run.
- Shared code lives in `docqa_core` only. The eval package must not depend on the rest of the stack, so it can run in CI and on a laptop without infrastructure.
- Local development needs Docker Desktop for the infrastructure services. Tests marked `integration` need those services running.
- Temporal and Langfuse add operational weight. Both are accepted for M0 so that workflow and LLM-trace concerns are not retrofitted later.
- Choices of hosting, LLM provider and data residency are not made here. See ADRs 0002 to 0004.
