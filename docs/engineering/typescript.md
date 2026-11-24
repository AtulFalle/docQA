# TypeScript standards

Applies to `apps/web`, `apps/backend`, `libs/shared/*` and the e2e projects. Source of truth for lint rules is the root `eslint.config.mjs`; for compiler options it is `tsconfig.base.json`; for formatting it is `.prettierrc`. Angular-specific rules are in [angular.md](angular.md), NestJS rules in [nestjs.md](nestjs.md).

Every rule is tagged:

- **[Enforced: tool/rule]** a tool fails the build, the commit or CI.
- **[Review]** no tool catches it; reviewers check it.

## Compiler

`tsconfig.base.json` sets `strict`, `noImplicitOverride`, `noImplicitReturns` and `noFallthroughCasesInSwitch`. Projects extend it and must not turn these off. **[Enforced: `tsc` in `typecheck`]**

- Do not add `// @ts-ignore`. Use `// @ts-expect-error <reason>` only when the error is known and tracked. **[Review]**
- Prefer `unknown` over `any` for data you have not parsed yet, then narrow it or validate it with zod at the edge. **[Review]**

## Lint rules (root `eslint.config.mjs`)

Enforced by `@typescript-eslint` and core ESLint on `*.ts`:

| Rule | What it means |
|------|---------------|
| `@typescript-eslint/no-explicit-any` | No `any`. **[Enforced]** |
| `@typescript-eslint/no-non-null-assertion` | No `value!`. Narrow with a check or throw a typed error. Relaxed only in spec and e2e files. **[Enforced]** |
| `@typescript-eslint/consistent-type-imports` | Type-only imports use `import type` / inline `type` (`fixStyle: inline-type-imports`). **[Enforced]** |
| `@typescript-eslint/no-unused-vars` | Unused names fail. Prefix with `_` only when the position is fixed (e.g. a callback argument). **[Enforced]** |
| `eqeqeq` | `===` and `!==` only. **[Enforced]** |
| `no-console` | Use the logger (NestJS: `nestjs-pino`). **[Enforced]** |
| `complexity` (10) | Split a function that needs more than 10 independent paths. **[Enforced]** |
| `max-depth` (4) | Guard clauses beat nesting. **[Enforced]** |
| `max-params` (6) | Pass an options object instead of a seventh argument. Relaxed only in spec and e2e files. **[Enforced]** |
| `no-restricted-imports` | Banned packages below. **[Enforced]** |

```ts
// bad
const user = users.find((u) => u.id == id)!;
console.log(user.email);

// good
const user = users.find((u) => u.id === id);
if (!user) {
  throw new UserNotFound(id);
}
logger.info({ userId: user.id }, 'user.lookup.found');
```

### Banned packages

- `axios`: use `fetch` in the backend and Angular `HttpClient` in the web app. **[Enforced: no-restricted-imports]**
- `lodash`: use native JS, or add a small targeted helper. **[Enforced: no-restricted-imports]**

Adding a dependency: justify it in the PR, check its licence (dependency-review runs in CI), and add it to the owning project's `package.json` or `project.json` only. **[Review]**

### Changing a rule

Rule changes are their own PR with a reason and CODEOWNERS review, the same as Python. **[Review]**

## Formatting

Prettier owns formatting: single quotes, 100 columns, trailing commas `all` (`.prettierrc`). ESLint stylistic rules are off, so do not argue style in review. Run `pnpm format` before committing; CI runs `pnpm format:check`. **[Enforced: Prettier check]**

## Module boundaries (Nx tags)

Each project carries tags in its `project.json`. The root config enforces who may import whom with `@nx/enforce-module-boundaries`. **[Enforced: `@nx/enforce-module-boundaries`]**

| Tag | May depend on |
|-----|---------------|
| `scope:web` (`apps/web`) | `scope:web`, `scope:shared` |
| `scope:backend` (`apps/backend`) | `scope:backend`, `scope:shared` |
| `scope:shared` (`libs/shared/*`) | `scope:shared` only |
| `type:contracts` (`libs/shared/contracts`) | `type:contracts` only |

- Web and backend never import each other. Cross-app types go through `@docqa/contracts`. **[Enforced]**
- Contracts hold types only, with no runtime code that depends on the apps. **[Review]**: no lint rule checks "type-only" yet.
- Import the public entry point (`@docqa/contracts`), never a deep path into another project. **[Review]**

## Shared contracts workflow

`libs/shared/contracts` (`@docqa/contracts`) is the single definition of request and response shapes that cross the browser/backend boundary.

1. Change the type in `libs/shared/contracts/src`.
2. Run `pnpm nx affected -t typecheck` and confirm both `web` and `backend` compile.
3. Update the backend handler and the Angular caller in the same PR.

```ts
// bad: web re-declares the response shape and drifts from the backend
interface DocumentDto { id: string; title: string }

// good
import type { DocumentSummary } from '@docqa/contracts';
```

## Naming

- Files and folders: `kebab-case.ts`. Suffixes name the role where the framework uses them: `.service.ts`, `.controller.ts`, `.module.ts`, `.spec.ts`, `.e2e-spec.ts`. **[Review]**
- Types, interfaces and classes: `PascalCase`. Functions, variables and properties: `camelCase`. Module constants: `UPPER_SNAKE_CASE`. **[Review]**
- No `I` prefix on interfaces. Name what a value is, not its type (`documents`, not `documentArray`). **[Review]**
- Boolean names read as questions: `isDeleted`, `hasAccess`. **[Review]**
- Use `const` by default and literal unions instead of enums for closed sets (`type Status = 'queued' | 'done'`). Use `as const` for lookup objects. **[Review]**

## Error handling

- Throw `Error` subclasses with a stable `code` field. Do not throw strings or plain objects. **[Review]**
- Catch as `unknown` and narrow: `catch (error: unknown) { ... }`. Strict mode makes `useUnknownInCatchVariables` the default. **[Enforced: tsc strict]**
- Never swallow. An empty `catch {}` is a bug. Log with context, then rethrow or translate. **[Review]**
- Translate errors at the edge only: HTTP filter in the backend, `ApiClient` error mapping in the web app. Services throw domain errors. **[Review]**

```ts
// bad
try {
  await save(doc);
} catch {}

// good
try {
  await save(doc);
} catch (error: unknown) {
  logger.error({ err: error, docId: doc.id }, 'document.save.failed');
  throw error;
}
```

## Async

- Every outbound call has a timeout. Use `AbortSignal.timeout(ms)` with `fetch`, and the `HttpClient` timeout in Angular. **[Review]**
- Never fire and forget. Await the promise, or hand it to a queue that owns the error. Use `Promise.all` or `Promise.allSettled` deliberately. **[Review]**
- Do not block the event loop in the backend: no `*Sync` fs or crypto calls in request paths. **[Review]**

```ts
// bad: no timeout, hangs the request when ai-api stalls
const res = await fetch(url, { method: 'POST', body });

// good
const res = await fetch(url, {
  method: 'POST',
  body,
  signal: AbortSignal.timeout(5_000),
});
```

## Secrets and config

- No secrets, tokens, or real hosts in code, tests or fixtures. Read config through the typed config layer (see [nestjs.md](nestjs.md), [angular.md](angular.md)). **[Review]**
- `gitleaks` scans every push. **[Enforced: `Security / secrets`]**
- Do not log request bodies, document text, tokens or cookies. **[Review]**

## Complexity and size

- A function with several responsibilities gets split. Complexity over 10 fails lint, so split first and do not add a disable comment. **[Enforced: complexity]** **[Review: size]**
- Suppressing a lint rule needs a reason on the same line: `// eslint-disable-next-line rule-name -- reason`. Bare disables are rejected in review. **[Review]**

## Checks to run locally

```bash
pnpm nx affected -t lint typecheck test build
pnpm format:check
```
