---
name: shared-models
description: How to add or change the shared API models in libs/shared/contracts (@docqa/contracts), which both the Angular web app and the NestJS backend use for request payloads, response bodies, the error envelope and domain value sets. Use whenever an endpoint's request or response shape changes, a new endpoint or entity is added, or the UI needs a type for API data.
---

# Shared models (@docqa/contracts)

`libs/shared/contracts` is the one place API shapes live. Web and backend both import it, so a change breaks whichever side hasn't caught up. Details are in `libs/shared/contracts/README.md`.

## Rules (lint-enforced)

- **Data only:** `interface`, `type`, and `as const` arrays with a derived union. No functions, classes, `enum`, decorators or zod.
- **No dependencies:** import only sibling model files, by relative path.
- **Consumers import from the root:** `import type { DocumentSummary } from '@docqa/contracts'`.
- **Never redeclare** an API shape in `apps/web` or `apps/backend`. If you need it on both sides, it belongs here.

## Where things go

```
libs/shared/contracts/src/lib/
  common/      api-error, pagination (PageQuery, Page<T>), primitives (Id, IsoDateTime)
  system/      health, info
  <domain>/    <entity>.models.ts: documents/, access/, jobs/, tenants/, …
```

Export every new file from `src/index.ts`.

## Naming and wire format

| Kind | Pattern | Example |
| --- | --- | --- |
| Response body | `<Thing>Response` or the entity name | `ReadinessResponse`, `DocumentSummary` |
| Request body | `<Verb><Thing>Request` | `CreateDocumentRequest` |
| Query | `<Thing>Query` (extends `PageQuery` for lists) | `DocumentListQuery` |
| List | `Page<T>` | `Page<DocumentSummary>` |
| Value set | `UPPER_SNAKE` const + union | `DOCUMENT_STATUSES` / `DocumentStatus` |

- Ids are `Id`, timestamps are `IsoDateTime` (strings on the wire). Optional fields use `?:`; use `| null` only when the API really sends `null`.
- Properties are camelCase. Document any non-obvious field with a `/** */` comment, because the comment shows up in both apps.
- A value set shared with Python must match the `StrEnum` in `libs/py-core/src/docqa_core/value_sets.py` exactly (`test_core_value_sets.py` checks it).

## Adding an endpoint, end to end

1. **Model:** add the request and response types in `lib/<domain>/<entity>.models.ts` and export them.
2. **Backend:** a zod schema typed `z.ZodType<CreateXRequest>` validates input; the controller returns `Promise<XResponse>`; the service maps Prisma rows to the model.
3. **Web:** `this.api.post<XResponse>('x', body)` in a feature data service, with the types imported from `@docqa/contracts`.
4. **Verify:** `pnpm nx run-many -t lint typecheck test -p contracts web backend`. Both apps must compile.
5. Land the model, the backend and the web changes in **one PR**.

Breaking change (a field removed, renamed or narrowed)? Add the new field first, migrate both sides, then remove the old field in a later PR. Note it in the PR's "Breaking changes" section.
