# Engineering standards

Concise, opinionated rules for docQA. Every rule is tagged:

- **[Enforced: tool/rule]** a tool fails the build or the commit. Source of truth: `pyproject.toml` for Python, `eslint.config.mjs`, `tsconfig.base.json` and `.prettierrc` for TypeScript.
- **[Review]** no tool catches it; reviewers check it (see `git-and-reviews.md`).

| Doc | Covers |
|-----|--------|
| [typescript.md](typescript.md) | Strict TS, ESLint rules, banned packages, Nx module boundaries, shared contracts, async |
| [angular.md](angular.md) | Standalone and OnPush components, signals, control flow, ApiClient, forms, accessibility, budgets |
| [nestjs.md](nestjs.md) | Modules, validation, typed config, logging, errors, health, calls to ai-api, Prisma tenancy |
| [python.md](python.md) | Style, typing, errors, async, config, logging, module boundaries |
| [fastapi.md](fastapi.md) | Routes, schemas, errors, auth, pagination, idempotency |
| [database.md](database.md) | SQLAlchemy, tenant context and RLS, Alembic, zero-downtime changes |
| [temporal.md](temporal.md) | Workflow determinism, activities, retries, versioning |
| [testing.md](testing.md) | Pyramid, naming, markers, coverage ratchet, flaky tests |
| [observability.md](observability.md) | Logs, traces, metrics, cost attribution |
| [security.md](security.md) | Untrusted documents, tenant/ACL filtering, secrets, containers |
| [rag-and-llm.md](rag-and-llm.md) | Prompts, model interfaces, citations, eval evidence |
| [docker-and-infra.md](docker-and-infra.md) | Images, compose, hadolint |
| [ci-cd.md](ci-cd.md) | Pipeline stages, branch protection, releases |
| [git-and-reviews.md](git-and-reviews.md) | Branching, commits, PRs, review checklist, CODEOWNERS |

## Quality gates

Python gates are live and blocking. The TypeScript gates (`CI / js`, `CI / e2e-web`, `Security / js-deps`, the web and backend Trivy scans, CodeQL for JavaScript/TypeScript) are the target state: their workflow jobs are added with the TypeScript apps, and each row is blocking once its job exists. "Workflow / job" is where to look when one fails.

| Gate | Tool | Local | CI workflow / job |
|------|------|-------|-------------------|
| Lint (bugs, security, complexity, docstrings, banned APIs) | `ruff check` | pre-commit | `CI / lint` |
| Format | `ruff format --check` | pre-commit | `CI / lint` |
| Architecture boundaries | `lint-imports` (import-linter contracts in `pyproject.toml`) | pre-push | `CI / lint` |
| Declared vs imported deps | `deptry` per package | `make deps-check` | `CI / lint` |
| Types (strict) | `mypy` | pre-push | `CI / typecheck` |
| Unit + integration tests, coverage floor | `pytest --cov` (`fail_under` in `pyproject.toml`) | pre-push (unit only) | `CI / test` |
| Cross-tenant leak test (RLS) | `libs/py-core/tests/test_core_rls.py` | `make test` (needs Postgres) | `CI / test` |
| Prisma migrations apply + schema drift | `pnpm db:migrate`, then `pnpm db:drift` (`prisma migrate diff --exit-code`) | `pnpm db:migrate`, `pnpm db:drift` | `CI / test` |
| Python mirror contract | `libs/py-core/tests/test_core_schema_contract.py` | `make test` (needs migrated Postgres) | `CI / test` |
| Prettier format | `prettier --check` (`.prettierrc`) | `pnpm format:check` | `CI / js` |
| ESLint incl. Nx module boundaries | `eslint` via `@nx/eslint`, root `eslint.config.mjs` | `pnpm nx affected -t lint` | `CI / js` |
| TypeScript typecheck (strict) | `tsc` per project | `pnpm nx affected -t typecheck` | `CI / js` |
| Angular + Nest unit tests | Vitest (web), Jest (backend) | `pnpm nx affected -t test` | `CI / js` |
| Production builds incl. Angular budgets | `nx build`, Angular build budgets | `pnpm nx affected -t build` | `CI / js` |
| Playwright e2e (API mocked) | `apps/web-e2e` | `pnpm nx e2e web-e2e` | `CI / e2e-web` |
| JS dependency CVEs (high and above) | `pnpm audit --audit-level high` | `pnpm audit --audit-level high` | `Security / js-deps` |
| Container CVEs, web and backend images | Trivy | — | `Security / image-scan` (also weekly) |
| JavaScript/TypeScript static analysis | CodeQL `javascript-typescript` | — | `CodeQL` |
| Golden dataset validity | `docqa-eval validate` | `make eval-validate` | `CI / eval` |
| Dockerfile lint | hadolint | — | `CI / lint-infra` |
| Workflow lint | actionlint | — | `CI / lint-infra` |
| Images build, compose valid | buildx, `docker compose config` | `make docker-build` | `CI / docker` |
| Secret scan | gitleaks (+ `detect-private-key` hook) | pre-commit (key hook) | `Security / secrets` |
| Python dependency CVEs | pip-audit | `make audit` | `Security / python-deps` (also weekly) |
| New-dependency vulns + licence allowlist | dependency-review-action | — | `Security / dependency-review` (PRs) |
| Container CVEs (fixable HIGH/CRITICAL) | Trivy | — | `Security / image-scan` (also weekly) |
| Static analysis | CodeQL (Python + Actions, security-and-quality) | — | `CodeQL` |
| Conventional Commit PR title | action-semantic-pull-request | `commit-msg` hook | `PR hygiene` |

`make check` runs every fast Python gate in one go. Install hooks once with `make setup`. For TypeScript, run `pnpm nx affected -t lint typecheck test build` and `pnpm format:check`.

Coverage ratchet **[Enforced: coverage `fail_under`]**: when coverage rises, raise `fail_under` in the same or next PR. Never lower it without an ADR.

## Exception policy

- Suppress a lint finding on one line, with a reason: `# noqa: S603 — fixed argv, no user input`. Bare `# noqa` is rejected. **[Review]**
- Suppress a type error with a code and a reason: `# type: ignore[arg-type]  # httpx stub gap, see #123`. **[Enforced: mypy `ignore-without-code`]**
- Prefer fixing over ignoring. Prefer a narrow per-file ignore in `pyproject.toml` over many inline ones, and only for whole classes of files (tests).
- Changing a rule (select/ignore/threshold/contract) needs its own PR explaining why, and a note in the PR body of what breaks if reverted. **[Review: CODEOWNERS]**
- Tool versions are pinned exactly (`ruff==...`, `mypy==...`) so rules never shift under us. Dependabot proposes bumps; fix the fallout in the same PR. **[Enforced: pinned in `pyproject.toml`]**

## Definition of Done

A change is done when:

- [ ] All blocking gates above pass in CI.
- [ ] Behaviour is covered by tests, including the failure path and, for tenant-scoped features, the cross-tenant/ACL denial path.
- [ ] No new `# noqa` / `# type: ignore` without a reason.
- [ ] Logs, spans and metrics exist for new external calls and failure modes; nothing sensitive is logged.
- [ ] Retrieval, chunking, embedding or prompt change: eval results (Recall@k, MRR, faithfulness) are in the PR.
- [ ] Schema change: one reviewed Prisma migration, zero-downtime safe, RLS policy and `TENANT_SCOPED_TABLES` updated.
- [ ] Config added to `Settings` and `.env.example`; docs/ADR updated where behaviour or decisions changed.
- [ ] PR is under ~400 changed lines (or explains why not), has a Conventional Commit title, and is reviewed per CODEOWNERS.
