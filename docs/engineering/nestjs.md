# NestJS standards

Applies to `apps/backend` (NestJS 12, Prisma 7). The backend is the public API (`/api/v1`) and the system of record: it owns auth, tenancy, ACLs and the Postgres schema. General TypeScript rules are in [typescript.md](typescript.md); database rules that apply to Python too are in [database.md](database.md).

Every rule is tagged:

- **[Enforced: tool/rule]** a tool fails the build, the commit or CI.
- **[Review]** no tool catches it; reviewers check it.

## Modules and layering

- One module per feature under `src/app/<feature>/`: `<feature>.module.ts`, `<feature>.controller.ts`, `<feature>.service.ts`, `dto/` (only for things that are not in contracts). **[Review]**
- Controllers are thin: parse the request, call one service method, return the response type. No business rules, no Prisma calls, no `fetch` in controllers. **[Review]**
- Services hold the logic and the decisions about tenant and ACL. They do not know about HTTP (no `Request`, `Response`, status codes). **[Review]**
- Modules export only what other modules need. Do not import a sibling module's repository or Prisma queries. **[Review]**
- Module boundaries follow Nx tags: `apps/backend` is `scope:backend` and may import `libs/shared/*` only. **[Enforced: `@nx/enforce-module-boundaries`]**

```ts
// bad: controller decides tenant and queries Prisma directly
@Get(':id')
get(@Param('id') id: string, @Body() body: { tenantId: string }) {
  return this.prisma.document.findUnique({ where: { id } });
}

// good
@Get(':id')
getDocument(@Param('id') id: string, @CurrentTenant() tenant: TenantContext): Promise<DocumentDetail> {
  return this.documents.getDocument(tenant, id);
}
```

## Contracts and validation

- Request and response types come from `@docqa/contracts`. Do not redeclare them in the backend. **[Review]**
- Validate input at the edge with zod. Parse the body, query and params into the contract type before the service sees them. Use a pipe or a shared zod helper; do not trust `req.body` as typed. **[Review]**
- Responses are shaped by the service return type, not by passing Prisma models out. Never return a Prisma row that includes fields the client must not see (hashes, internal ACL rows). **[Review]**

```ts
export const CreateNoteBody = z.object({ title: z.string().min(1).max(200) });
export type CreateNoteBody = z.infer<typeof CreateNoteBody>;
```

## Configuration

- All config comes from a typed `ConfigService`, validated by zod at startup. The process fails fast when a required value is missing or malformed. **[Review]**
- Only `src/instrumentation.ts` reads `process.env`. Everything else reads `ConfigService` (or a typed slice of it). **[Review]**
- Every new setting: add it to the zod schema with a safe default (or none for secrets), and add a line to `.env.example`. **[Review]**
- Never import a config object as a global. Inject `ConfigService` or the slice you need. **[Review]**

```ts
// bad
const aiUrl = process.env.AI_API_URL ?? 'http://localhost:8001';

// good
const aiUrl = this.config.get('aiApi.baseUrl', { infer: true });
```

## Logging

- Use `nestjs-pino` (`Logger` from `nestjs-pino` or the injected `PinoLogger`). `console` is banned. **[Enforced: `no-console`]**
- Structured fields, event-style messages: `document.upload.accepted`, not a sentence with interpolated values. **[Review]**
- Every log line carries the request id and the OpenTelemetry trace id. The request id comes from `X-Request-Id` (generated if absent) and is echoed in the response. **[Review]**
- Redact `authorization`, `cookie`, `set-cookie`, password and token fields in the pino config. Never log document text, query text or prompts. **[Review]**

## Errors

- Throw domain errors (`DocumentNotFound`, `AccessDenied`) with a stable `code`. Do not throw `HttpException` from services. **[Review]**
- A single global exception filter maps errors to the error envelope from `@docqa/contracts`: `{ code, message, requestId }`. **[Review]**
- Clients never receive stack traces, SQL text, upstream bodies or internal hostnames. Log them server-side with the request id. **[Review]**
- Unknown errors become `500 INTERNAL` with a generic message. **[Review]**

## Versioning and routes

- URI versioning. Set the global prefix and the version once in `main.ts`: all routes are under `/api/v1`. **[Review]**
- Health endpoints are outside the version prefix (see below). **[Review]**
- Paginate every list endpoint with a limit and a cursor. No unbounded `findMany`. **[Review]**

## Health

- `GET /api/v1/health`: liveness. Returns 200 if the process runs. It does not call dependencies. **[Review]**
- `GET /api/v1/health/ready`: readiness, built with `@nestjs/terminus` (503 when a dependency is down). Checks Postgres (`SELECT 1` through Prisma) and the ai-api health endpoint with a short timeout. **[Review]**
- Kubernetes or compose probes use liveness for restarts and readiness for traffic. **[Review]**

## Calling the Python AI service

The `ai-api` service is internal. Only the backend calls it, over HTTP, with a typed client wrapper in one module. **[Review]**

- Every call has a timeout (`AbortSignal.timeout`). Set one per operation, and keep it short for interactive calls. **[Review]**
- Retry with exponential backoff and jitter only for idempotent calls (GET, or POST with an `Idempotency-Key`). Cap retries at 2. **[Review]**
- A circuit breaker comes later (see [rag-and-llm.md](rag-and-llm.md)). Do not hand-roll one per call site. **[Review]**
- The tenant is never taken from the client. The backend derives `tenantId` and the user's ACL scope from the authenticated session, and passes them to ai-api as trusted internal context. The client never sends a tenant id to ai-api. **[Review]**
- Send `X-Request-Id` and the trace headers on every call. **[Review]**
- Log the upstream status, duration and attempt count. Do not log the request body. **[Review]**

## Prisma and tenancy

Prisma 7 with the Postgres adapter owns the schema (`apps/backend/prisma/schema.prisma`) and migrations (`apps/backend/prisma/migrations`). **[Review]**

- Every tenant-scoped query goes through `PrismaService.withTenant(tenantId, fn)`. It opens one transaction, runs `set_config('app.tenant_id', ..., true)` first, and then runs `fn` with the transaction client. **[Review]**
- Queries still filter on `tenantId` explicitly. RLS is defence in depth, not the filter. **[Review]**
- `tenantId` comes from the auth context, never from a body, query or path parameter. **[Review]**
- Do not hold a transaction open across a network call (ai-api, storage, LLM). **[Review]**
- Bound every query: `take`, cursor pagination, and `statement_timeout` on the application role. **[Review]**

```ts
// good
return this.prisma.withTenant(tenant.id, (tx) =>
  tx.document.findFirst({ where: { tenantId: tenant.id, id: documentId } }),
);
```

### Migrations and schema changes

- Migrations are committed SQL, one reviewed migration per PR. Generated SQL is a draft and is read before commit. **[Review]**
- Zero-downtime rules (expand, then contract) apply: see [database.md](database.md). **[Review]**
- A new tenant-scoped table needs, in the same migration: `tenant_id` FK, `ENABLE` and `FORCE ROW LEVEL SECURITY`, the `tenant_isolation` policy (raw SQL, since Prisma cannot express RLS), and an entry in `TENANT_SCOPED_TABLES`. **[Review; the schema contract test checks the Python mirror]**
- Update the Python mirror (`libs/py-core`, SQLAlchemy models) in the same PR. **[Enforced: `test_core_schema_contract` in `CI / test`]**
- Drift between the Prisma schema and migrations fails CI. **[Enforced: `pnpm db:drift`, `CI / test`]**

## Security

- Authentication and authorisation run as Nest guards. Every route is protected unless it is explicitly marked public. **[Review]**
- Input size limits on bodies and uploads are set in the platform adapter. **[Review]**
- No secrets in code or in logs. **[Enforced: gitleaks]**

## Testing

- Unit tests: Jest with `@nestjs/testing`. Build the module with mocked providers, and test the service logic and error codes. **[Enforced: `CI / js` (target)]**
- E2E tests (`apps/backend-e2e`): plain `fetch` against a running backend, with the AI service stubbed. Assert status, the error envelope and the tenant-denial path. **[Enforced: `CI / js` (target)]**
- Every tenant-scoped endpoint has a test that another tenant's id returns 404 (not 403, so existence is not leaked). **[Review]**

```ts
it('returns 404 for a document in another tenant', async () => {
  const res = await fetch(`${baseUrl}/api/v1/documents/${otherTenantDocId}`, {
    headers: { authorization: tenantAToken },
    signal: AbortSignal.timeout(5_000),
  });
  expect(res.status).toBe(404);
});
```

## Checks to run locally

```bash
pnpm nx lint backend
pnpm nx test backend
pnpm nx e2e backend-e2e
pnpm db:migrate
pnpm db:drift
```
