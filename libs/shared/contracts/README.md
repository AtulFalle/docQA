# @docqa/contracts: shared models

The single source of truth for data that crosses the browser ↔ backend boundary: request payloads, response bodies, the error envelope, and the domain value sets (statuses, permissions). `apps/web` (Angular) and `apps/backend` (NestJS) both import from here. Change a model and both sides fail to compile until they agree.

## Layout

```
src/
  index.ts                      public API: re-exports every model file
  lib/
    common/                     cross-cutting: api-error, pagination, primitives (Id, IsoDateTime)
    system/                     health, info
    <domain>/<entity>.models.ts one folder per domain: documents, access, jobs, tenants, …
```

## Rules (lint-enforced in `eslint.config.mjs`)

- **Data only:** `interface`, `type`, and `as const` value lists with a derived union. No functions, classes, `enum` or decorators.
- **No dependencies:** import only other model files, by relative path. No Angular, NestJS, zod or Prisma.
- **Import from the package root:** `import type { ReadinessResponse } from '@docqa/contracts'`, never a deep path.

## Naming

| Kind | Name | Example |
| --- | --- | --- |
| Response body | `<Thing>Response` or the entity name | `ReadinessResponse`, `DocumentSummary` |
| Request body | `<Verb><Thing>Request` | `CreateDocumentRequest` |
| Query params | `<Thing>Query` | `DocumentListQuery extends PageQuery` |
| List response | `Page<T>` | `Page<DocumentSummary>` |
| Closed value set | `UPPER_SNAKE` array + `PascalCase` union | `DOCUMENT_STATUSES` / `DocumentStatus` |

Wire formats: ids are `Id` (UUID string), timestamps are `IsoDateTime` (ISO-8601 string), and optional fields are `?:` (never `| null`, unless the API really sends `null`).

## Workflow

1. Add or change the model here and export it from `src/index.ts`.
2. Run `pnpm nx run-many -t typecheck`; `web` and `backend` must both compile.
3. Update the NestJS handler and the Angular caller in the same PR.
4. Backend: validate incoming payloads at the edge with a zod schema typed against the model (`z.ZodType<CreateDocumentRequest>`), so runtime validation and the shared type can't drift.
5. Values shared with Python (statuses, permissions) must match the `StrEnum`s in `libs/py-core`.
