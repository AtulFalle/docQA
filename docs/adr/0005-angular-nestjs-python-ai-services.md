# 0005. Angular UI, NestJS backend, Python internal AI services

- Status: Accepted
- Date: 2026-11-24

## Context

ADR 0001 put everything in a Python uv workspace with a FastAPI service as the public API. The product needs a web UI, and the public API, authentication, tenancy, ACLs and the database schema are better served by a dedicated backend with strong typing end to end from UI to API. The AI work (retrieval, answer generation, ingestion, evaluation) stays in Python where the ecosystem is strongest.

## Decision

- **Angular UI** (`apps/web`): the browser client.
- **NestJS backend** (`apps/backend`): the public API (`/api/v1`) and system of record. It owns auth, tenancy and ACLs, and owns the Postgres schema through Prisma migrations (`apps/backend/prisma`), including row-level security policies written as raw SQL in migrations.
- **Python internal AI services**: FastAPI `ai-api` (`services/ai-api`) for retrieval and answers, Temporal ingestion workers (`services/ingestion-worker`), and the eval harness (`eval`). They are never exposed to browsers.
- **Tooling**: Nx + pnpm for the TypeScript apps; Python stays a uv workspace (`libs/py-core`, `services/*`, `eval`).
- **Request path**: Browser -> Angular (`/api` proxy) -> NestJS `/api/v1` -> internal HTTP -> Python `ai-api`.

## Consequences

- Two languages and two toolchains in one repository; CI runs both.
- The NestJS-to-Python contract is an OpenAPI document; clients are generated or validated against it.
- Alembic is removed. The Python SQLAlchemy models in `docqa_core.db` become a mirror of the Prisma schema, guarded by `libs/py-core/tests/test_core_schema_contract.py` and the cross-tenant RLS test, both run against a database migrated by Prisma.
- Schema drift is checked in CI with `prisma migrate diff --exit-code`.
- Auth and ACL decisions are made in the backend and passed to the AI services as trusted internal context.
