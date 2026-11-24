# Git and review standards

## Workflow

- **Trunk-based**: `main` is always deployable; everything lands through a PR. Branches live hours to a couple of days, not weeks. **[Enforced: branch protection]**
- Branch names `type/short-topic`: `feat/ingest-ocr`, `fix/acl-cache`, `docs/m0-readme`, `chore/bump-ruff`.
- Rebase on `main` before review; **squash merge** only (linear history). The PR title becomes the commit message.
- Unfinished work ships behind a setting/feature flag, not on a long-lived branch.
- Never force-push `main`; force-push your own branch only before review starts or with `--force-with-lease`.

## Conventional Commits

Format `type(scope): imperative summary`, under 72 characters. **[Enforced: semantic PR title check]**

| Type | Use |
|------|-----|
| `feat` | User-visible capability |
| `fix` | Bug fix |
| `perf` | Performance improvement |
| `refactor` | No behaviour change |
| `test` | Tests only |
| `docs` | Documentation, ADRs |
| `build` | Dependencies, packaging, Dockerfiles |
| `ci` | Workflows and gates |
| `chore` | Housekeeping |

- Scopes: `core`, `ai-api`, `ingestion-worker`, `web`, `backend`, `eval`, `infra`, `migrations`, `docs`.
- Body explains **why**. Breaking change: `!` after scope and a `BREAKING CHANGE:` footer.

## Pull requests

- **Small**: aim for under ~400 changed lines (excluding generated files and lockfiles). Split refactors from behaviour changes, and migrations from the code that uses them when possible (expand/contract).
- Fill the PR template: what and why, how tested, eval impact, migration impact, security/ACL impact, rollout and rollback.
- Link the milestone/issue/ADR. Include screenshots, sample output or eval tables where relevant.
- Self-review the diff first; remove debug code; keep unrelated changes out.
- Draft PRs for early feedback; mark ready when CI is green.
- Respond to every comment; the author resolves their own threads after fixing, the reviewer resolves discussion threads.

## Review checklist

Reviewers verify (no tool catches these). Block on any failure:

1. **Correctness**: does it do what the description says; edge cases, empty/large/malformed input, concurrency, idempotency of retries.
2. **Tenant and ACL safety**: tenant derived from auth; `set_tenant_context` called; queries filter by tenant; ACL as pre-filter; fail closed; cross-tenant test exists.
3. **Tests**: new behaviour and failure paths covered; no sleeps/network; names follow `testing.md`; coverage floor ratcheted if raised.
4. **Observability**: structured events, no sensitive data in logs/spans, external calls traced, errors have context.
5. **Eval impact**: retrieval/chunking/prompt/model change includes Recall@k, MRR, faithfulness before/after, within threshold.
6. **Migration safety**: one migration, reviewed Prisma-generated SQL, zero-downtime pattern, RLS + `TENANT_SCOPED_TABLES`, concurrent index in its own migration.
7. **Security**: untrusted input validated and bounded; no secrets; new dependency justified; no new exceptions to rules without a reason.
8. **Design**: respects import boundaries, thin routes, config through `Settings`, simple over clever; naming and docs clear.
9. **Operations**: timeouts, retries, resource use, rollout/rollback, docs and `.env.example` updated.

Reviewers: be specific and kind; prefer questions to commands; label nits (`nit:`); approve when remaining items are non-blocking. Authors: do not merge with unresolved blocking comments.

## Who approves what (CODEOWNERS)

`.github/CODEOWNERS` routes review. With "require Code Owner review" on, these paths need an owner approval:

| Path | Why it is sensitive |
|------|--------------------|
| `*` | Default owner |
| `/apps/backend/prisma/` | Schema and data safety |
| `/libs/py-core/src/docqa_core/db/` | Models, sessions, tenant context, RLS |
| `/.github/` | CI, permissions, supply chain |
| `/eval/datasets/` | Golden data defines "correct" |

Add team handles (for example `@org/platform`, `@org/search`) as the team grows; keep the most specific rule last. Changes to quality rules (`pyproject.toml` lint/mypy/coverage/importlinter sections) are reviewed with the same care as `.github/`; add them to CODEOWNERS when a team exists.
