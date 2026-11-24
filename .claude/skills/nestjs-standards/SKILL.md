---
name: nestjs-standards
description: How to write NestJS code in docQA (apps/backend). Covers feature modules, thin controllers, typed services, zod validation against @docqa/contracts models, config, errors, Prisma tenancy, calls to the Python ai-api, size and typing limits, and tests. Use whenever you create or change anything under apps/backend, including modules, controllers, services, Prisma schema and migrations, filters and specs.
---

# NestJS standards (apps/backend)

Full rules: `docs/engineering/nestjs.md`, `docs/engineering/typescript.md` and `docs/engineering/database.md`. **[Lint]** means a tool fails the build.

## Hard limits

| Rule | Limit |
| --- | --- |
| File size | ≤ 400 lines **[Lint]** |
| Function / method | ≤ 50 lines, complexity ≤ 10, nesting ≤ 4, ≤ 6 params **[Lint]** |
| Types | no `any` **[Lint]**, no non-null `!` **[Lint]**, explicit return types on every function **[Lint]** |
| Imports | `apps/backend` may import only `scope:backend` and `scope:shared` libs **[Lint]** |

Near a limit? Extract a private method, a pure helper (`*.utils.ts` + spec), or a new provider. Don't disable the rule.

## Layout and layering

```
src/<feature>/
  <feature>.module.ts       exports only what other modules need
  <feature>.controller.ts   thin: parse → one service call → return contract type
  <feature>.service.ts      business rules, tenant/ACL decisions; no HTTP types
  <feature>.schemas.ts      zod schemas typed against @docqa/contracts models
  *.spec.ts                 unit tests next to the code
```

- **Controllers** parse input, call one service method, and return the response model. No Prisma, no `fetch`, no business rules.
- **Services** don't know about HTTP (no `Request`, `Response`, status codes). They throw domain or Nest exceptions, and `AllExceptionsFilter` maps those to `ApiErrorResponse`.
- **Dependency injection:** constructor injection with `private readonly`. Keep the constructor's parameter types as value imports (decorator metadata needs them).

## Contracts and validation

```ts
// feature.schemas.ts
export const createDocumentSchema: z.ZodType<CreateDocumentRequest> = z.object({
    title: z.string().min(1).max(200),
});

// feature.controller.ts
@Post()
create(@Body(new ZodValidationPipe(createDocumentSchema)) body: CreateDocumentRequest): Promise<DocumentSummary> {
    return this.documents.create(body);
}
```

- Request and response types come from `@docqa/contracts`; never redeclare them here (see the `shared-models` skill).
- Validate body, query and params with zod at the edge through one shared pipe, `src/common/zod-validation.pipe.ts`. It doesn't exist yet: create it with the first endpoint that takes input, and have it throw `BadRequestException` with the zod issues. Never trust `req.body` as typed.
- Map Prisma rows to the contract model in the service. Never return a raw Prisma row.

## Config, errors, logging

- Config only through `ConfigService<Env, true>` (`src/config/env.ts`, zod-validated). `process.env` is read only in `instrumentation.ts`.
- Error bodies always follow `ApiErrorResponse` and never include stack traces. Readiness failures keep the Terminus body (503).
- Log with the injected pino `Logger` and structured fields, never `console`. Don't log document content, tokens or PII.

## Data and the AI service

- Every Prisma query runs inside the tenant context (RLS). Schema changes need a migration in `apps/backend/prisma/migrations` that is safe for zero-downtime deploys, and a clean `pnpm db:drift`.
- Call ai-api with `fetch`, a timeout (`AbortSignal.timeout`) and the propagated request id. Map its failures to 502/503, never 500 with internals.

## Tests

- Unit-test services with Prisma and fetch mocked; test controllers through the Nest testing module. Name tests by behaviour.
- e2e (`backend-e2e`) for API contracts: status code + body shape against the contract model.

## Before you finish

```bash
pnpm nx run-many -t lint typecheck test build -p backend contracts
DATABASE_URL=… pnpm db:drift        # when the schema changed
```
