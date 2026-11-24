# Contributing to docQA

## Branching

- `main` is always deployable. Direct pushes are not allowed; use a pull request.
- Work on short-lived branches named by type and topic: `feat/ingest-ocr`, `fix/acl-cache`, `docs/m0-readme`.
- Keep branches small. Rebase on `main` before review, and squash-merge when approved.

## Commits: Conventional Commits

Commit subjects use the form `type(scope): summary`, in the imperative and under 72 characters.

- Types: `feat`, `fix`, `perf`, `refactor`, `test`, `docs`, `build`, `ci`, `chore`, `revert`.
- Scopes (optional): `web`, `backend`, `ai-api`, `worker`, `core`, `contracts`, `db`, `eval`, `infra`, `ci`, `deps`, `docs`, `m0`. The `commit-msg` hook and the PR title check reject any other scope.
- Use a body for the why, and add `BREAKING CHANGE:` in the footer when needed.
- `git commit` opens [.gitmessage](.gitmessage) as the template (`make setup` sets it; or run `git config commit.template .gitmessage`).

Examples:

```
feat(ai-api): add request id to every response
fix(core): reset tenant context on session checkout
```

## Local setup

1. Install Node 24 (with corepack), Docker Desktop, uv and Python 3.12 (see the README prerequisites).
2. Install workspace dependencies and the git hooks:
   - TypeScript: `corepack enable` then `pnpm install`
   - Python, PowerShell or make: `uv sync --all-packages --group dev` then `uv run pre-commit install`
   - Or `make setup` for the Python side
3. Run the TypeScript checks before pushing (Nx runs only what your change affects):
   - `pnpm nx affected -t lint typecheck test build` and `pnpm format:check`
   - `pnpm nx serve web` starts the web app and the backend for manual testing
   - `pnpm db:migrate` applies Prisma migrations; `pnpm db:drift` checks the schema against them
4. Run the Python checks before pushing:
   - `uv run ruff check .` and `uv run ruff format --check .`
   - `uv run mypy libs/py-core/src services/ai-api/src services/ingestion-worker/src eval/src`
   - `uv run pytest -m "not integration"` for quick checks, or `uv run pytest` with infra running

Pre-commit runs trailing-whitespace and end-of-file fixes, YAML and TOML checks, private-key detection, LF line endings, Ruff lint and Ruff format on every commit. If a hook changes files, stage them and commit again.

## Architecture decisions (ADRs)

Decisions that affect structure, stack, data handling or operations are recorded in `docs/adr/`.

1. Copy `docs/adr/template.md` to the next free number, for example `0005-short-title.md`.
2. Open a PR with status `Proposed` and the options laid out.
3. Accept it in a later PR once the open questions are answered. Accepted ADRs are not edited; supersede them instead.
4. Update `docs/adr/README.md` and the relevant milestone file.

## Engineering standards (mandatory reading)

Read [docs/engineering/README.md](docs/engineering/README.md) before your first PR. Every rule there is tagged as CI-enforced or reviewer-checked. For TypeScript work, also read:

- [docs/engineering/typescript.md](docs/engineering/typescript.md): strict TS, ESLint rules, module boundaries, shared contracts
- [docs/engineering/angular.md](docs/engineering/angular.md): components, signals, HTTP through `ApiClient`, accessibility, budgets
- [docs/engineering/nestjs.md](docs/engineering/nestjs.md): modules, validation, config, errors, calls to ai-api, Prisma tenancy

In short, a PR must pass:

- `pnpm nx affected -t lint typecheck test build`, `pnpm format:check`, and the Playwright e2e for the web app (`CI / js`, `CI / e2e-web`). A change to `libs/shared/contracts` must compile in both `web` and `backend`.
- `ruff` lint and format (also in pre-commit) and `mypy --strict`.
- `import-linter` boundaries and `deptry` (as the CI jobs land).
- `pytest` with the coverage floor (`fail_under`, a ratchet: raise it, never lower it without an ADR), plus the Python schema contract test against a Prisma-migrated database.
- Eval dataset validation, and eval results in the PR for any retrieval, chunking or prompt change.
- Security and supply-chain checks: gitleaks, pip-audit, Trivy, CodeQL, dependency review, hadolint, actionlint.
- A Conventional Commit PR title, and Code Owner review for sensitive paths (`.github/CODEOWNERS`).

Exceptions need a reason: `# noqa: CODE — reason` or `# type: ignore[code]  # reason`.

## Pull request checklist

Fill in the template. Before requesting review, confirm:

- [ ] Tests are added or updated, and the unit tests pass.
- [ ] Lint, format and mypy pass.
- [ ] Eval impact is stated: golden set or metrics changed, or no retrieval or answer change.
- [ ] A Prisma migration is included if the schema changed (zero-downtime safe).
- [ ] Security and ACL impact is considered: tenant isolation, document permissions, sensitive data in logs.
- [ ] Docs are updated where setup or behaviour changed.

A reviewer checks the milestone reference and the checklist before approving.
