# backend

NestJS 12 public API and system of record for DocQA. Global prefix `/api`, URI versioning (default `v1`).
Calls the internal Python AI service at `AI_SERVICE_URL`.

## Endpoints

| Method | Path                  | Description                                                        |
| ------ | --------------------- | ------------------------------------------------------------------ |
| GET    | `/api/v1/health`      | Liveness, no dependencies. `{ "status": "ok" }`                    |
| GET    | `/api/v1/health/ready`| Readiness: database ping + AI service `GET /healthz` (503 if down) |
| GET    | `/api/v1/info`        | `{ service, version, environment }`                                |

Errors use the `ApiErrorResponse` envelope (`statusCode`, `error`, `message`, `requestId`). `X-Request-ID` is echoed or generated.

## Environment variables

| Variable                      | Default                 | Notes                                  |
| ----------------------------- | ----------------------- | -------------------------------------- |
| `NODE_ENV`                    | `development`           | `development`, `test`, `production`    |
| `PORT`                        | `3000`                  |                                        |
| `DATABASE_URL`                | required                | Postgres URL                           |
| `AI_SERVICE_URL`              | `http://localhost:8001` |                                        |
| `LOG_LEVEL`                   | `info`                  | pino level                             |
| `SERVICE_NAME`                | `docqa-backend`         | Also OTel service name                 |
| `APP_VERSION`                 | `0.1.0`                 |                                        |
| `OTEL_ENABLED`                | `false`                 | Enables OpenTelemetry tracing          |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | unset                   | OTLP gRPC endpoint                     |

## Prisma workflow

Prisma is the source of truth for the Postgres schema.

1. Edit `prisma/schema.prisma`.
2. `pnpm db:migrate:dev` and commit the generated migration SQL.
3. New tenant-scoped tables (anything with `tenant_id`) must enable and force RLS and add the `tenant_isolation` policy
   (`tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid`, as USING and WITH CHECK) in the migration.
4. Update the Python mirror (`libs/py-core/src/docqa_core/db/models/`) in the same PR; a CI contract test compares them.

Other commands: `pnpm db:generate`, `pnpm db:migrate` (deploy), `pnpm db:drift`. The client is generated into
`src/generated/` (git-ignored) by the `prisma-generate` target, which build/serve/test/lint/typecheck depend on.
Use `PrismaService.withTenant(tenantId, tx => ...)` for tenant-scoped queries.

## Running

```
export DATABASE_URL=postgresql://user:pass@localhost:5432/docqa
pnpm db:migrate
pnpm start:backend
```

Docker: `docker build -f apps/backend/Dockerfile .` (runtime image); `--target migrate` for the migration runner.

## Tests

- Unit: `pnpm nx test backend`
- Typecheck: `pnpm nx typecheck backend`
- e2e (needs DATABASE_URL for serve): `pnpm nx e2e backend-e2e`
