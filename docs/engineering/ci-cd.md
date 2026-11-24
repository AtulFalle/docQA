# CI/CD standards

## Pipeline and what each job proves

| Workflow / job | Proves |
|-----|--------|
| `CI / lint` | ruff lint + format; import-linter boundaries; deptry dependency hygiene |
| `CI / lint-infra` | hadolint on both Dockerfiles; actionlint on all workflows |
| `CI / typecheck` | `mypy --strict` passes on all packages |
| `CI / js` | Prettier check; ESLint incl. Nx module boundaries; TypeScript typecheck; Angular (Vitest) and Nest (Jest) unit tests; production builds incl. Angular budgets. Runs `nx affected` |
| `CI / e2e-web` | Playwright e2e for `apps/web`, with the API mocked via `page.route` |
| `CI / test` | Applies Prisma migrations (`pnpm db:migrate`), then checks drift (`pnpm db:drift`) before Python tests; Python mirror contract test; unit + integration tests (incl. cross-tenant RLS leak test) against real Postgres; coverage >= floor |
| `CI / eval` | Golden dataset is valid against the sample corpus (later: retrieval metrics have not regressed) |
| `CI / docker` | Both images build; compose file is valid |
| `Security / *` | gitleaks, pip-audit, `pnpm audit --audit-level high` (`js-deps`), dependency-review (vulns + licence allowlist), Trivy image scan (ai-api, worker, web, backend); also weekly on schedule |
| `CodeQL` | No new code-scanning alerts (Python, Actions) |
| `PR hygiene` | PR title is a Conventional Commit (squash merge makes it the commit message) |

Rules:

- CI is the source of truth; "works locally" does not count. Anything CI enforces must be runnable locally with one command (see `CONTRIBUTING.md`, `make`).
- Jobs run in parallel; only `docker` depends on `lint`. Keep total PR feedback under ~10 minutes.
- Do not add `continue-on-error` to a required job. A non-blocking check is advisory and must say so in its name.
- Every gate must be deterministic: no network flakiness without retries, no dependence on external LLMs.

## Branch protection (enable on `main`)

GitHub: Settings, Branches, rule for `main`:

- Require a pull request before merging; at least **1 approval**, dismiss stale approvals on new commits, require review from Code Owners.
- Require status checks to pass, and **require branches to be up to date** before merging. Required checks: `lint`, `typecheck`, `test`, `js`, `e2e-web` (once the TypeScript jobs exist), `eval`, `docker`, `security` (once added), `pr-title`, CodeQL.
- Require conversation resolution.
- Require **linear history** (squash merge only; disable merge commits).
- **Do not allow force pushes** or deletions; include administrators.
- Restrict who can push tags `v*` (release tags are protected via a tag ruleset).
- Enable secret scanning + push protection, Dependabot alerts, and code scanning.

## Workflow hygiene

- **Pin actions**: third-party actions (anything outside `actions/*`, `github/*`, `docker/*`) are pinned to a full commit SHA with the version in a comment (`uses: org/action@<sha> # v1.2.3`). Tags are mutable: in March 2026 attackers force-pushed most `aquasecurity/trivy-action` tags to credential-stealing code (GHSA-69fq-xp46-6x23). Dependabot (`github-actions`) still updates SHA pins. **[Review]**
- **Least privilege**: top-level `permissions: contents: read`; grant extra (`packages: write`, `id-token: write`, `security-events: write`) only on the job that needs it. **[Review; CodeQL/actionlint flag some]**
- Never use `pull_request_target` with checkout of PR code. No untrusted input (`github.event.*.title`, branch names) interpolated into `run:` scripts; pass via `env:`. **[Enforced: actionlint, CodeQL]**
- Secrets only via GitHub secrets/OIDC, scoped to environments; not available to fork PRs.
- `concurrency` groups cancel superseded runs on PRs (never on `main` deploys).
- Set `timeout-minutes` on every job.

## Caching

- `astral-sh/setup-uv` with `enable-cache: true` (keyed by lockfile once `uv.lock` is committed; then use `uv sync --locked`).
- Docker builds use `cache-from/cache-to: type=gha` with a scope per image.
- Never cache secrets or `.env`; caches are not a source of truth.

## Release and tagging

- `main` is always deployable. CD (`cd.yml`) builds and pushes `ghcr.io/<owner>/docqa-ai-api` and `docqa-ingestion-worker` on pushes to `main` (tag `sha-<short>`) and `v*` tags.
- Releases use SemVer tags `vMAJOR.MINOR.PATCH` cut from `main`; the version comes from Conventional Commits (`feat` minor, `fix` patch, `BREAKING CHANGE` major). Changelog generated from commit history.
- Promote the **same image** (by digest) through environments; do not rebuild per environment.
- Images are scanned and (when chosen in ADR 0002) signed/attested before deploy.
- Migrations run as a separate pre-deploy step, are backward compatible with the previous app version (see `database.md`), and deploys are rollbackable by redeploying the prior image.
- Hotfix: branch from the release tag, `fix/...`, PR to `main`, tag a patch release. No direct pushes.
