<!--
PR title = squash commit on main. Use Conventional Commits:
  type(scope): summary   e.g. feat(backend): add document upload endpoint
types:  feat fix perf refactor test docs build ci chore revert
scopes: web backend ai-api worker core contracts db eval infra ci deps docs m0
-->

## Summary

<!-- What changes and why, in 2-4 sentences. -->

## Linked work

<!-- Issue, ADR or milestone item. Write "none" if there isn't one. -->

- Closes:
- ADR / milestone:

## Type of change

- [ ] Feature
- [ ] Bug fix
- [ ] Refactor / tech debt (no behaviour change)
- [ ] Performance
- [ ] Docs
- [ ] Build / CI / infra / dependencies
- [ ] Breaking change (describe below)

## Areas touched

- [ ] web (Angular)
- [ ] backend (NestJS)
- [ ] ai-api (Python)
- [ ] ingestion worker
- [ ] libs (py-core / shared contracts)
- [ ] database schema / Prisma migration
- [ ] infra / Docker / CI

## Changes

<!-- Main changes as bullets. Point reviewers to the parts that matter most. -->

-

## How it was tested

<!-- Commands you ran and what you checked by hand. Paste short results, not full logs. -->

- [ ] Unit tests: `pnpm nx affected -t test` / `uv run pytest -m "not integration"`
- [ ] Lint, format, typecheck: `pnpm nx affected -t lint typecheck`, `pnpm format:check`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`
- [ ] Build: `pnpm nx affected -t build`
- [ ] E2E: `pnpm nx e2e web-e2e` (UI or API flow changes)
- [ ] Manual check (steps below)

Manual steps:

## Screenshots / recordings

<!-- For UI changes: before and after. Otherwise delete this section. -->

## Database & migrations

- [ ] No schema change
- [ ] Prisma migration added in `apps/backend/prisma/migrations`, safe for zero-downtime deploys (additive, or split into expand/contract)

## Eval impact

- [ ] No retrieval, chunking, prompt or answer change
- [ ] Changed: eval results attached below (golden set metrics before and after)

## Security & privacy

- [ ] No impact
- [ ] Considered: tenant isolation (RLS), document ACLs, authn/authz, secrets, sensitive data in logs or traces

## Breaking changes, rollout & rollback

<!-- API or contract changes, new env vars, config or feature flags, deploy order, how to roll back. Write "none" if nothing applies. -->

## Docs

- [ ] Not needed
- [ ] Updated (README, ADR, `docs/`, milestone checklist, `.env.example`)

## Reviewer notes

<!-- Open questions, follow-ups, known limits. -->
