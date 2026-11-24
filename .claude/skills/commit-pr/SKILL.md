---
name: commit-pr
description: Commit the current changes and open a GitHub pull request the docQA way. Uses Conventional Commit messages from .gitmessage, runs the quality gates for the areas the change touches, then opens the PR with every section of .github/pull_request_template.md filled in. Use when the user asks to commit, push, open a PR or ship changes in this repo.
---

# Commit and open a PR (docQA)

Use this flow whenever you commit or open a PR in this repo. **Never** add a `Co-Authored-By: Claude` trailer or a "Generated with Claude Code" line.

## 1. Look at the change

- `git status` and `git diff` (plus `git diff --staged`). Know what every changed file does before you commit it.
- Leave out anything that doesn't belong: secrets, `.env`, scratch files, local-only config. If you're unsure about a file, ask.
- Split unrelated changes into separate commits, or separate PRs if they would be reviewed apart.

## 2. Branch

- Never commit to `main` (the `no-commit-to-branch` hook blocks it anyway).
- If you're on `main`, create `<type>/<short-topic>`, e.g. `feat/doc-upload` or `fix/acl-cache`.

## 3. Run the gates for what changed

Run only what the diff touches. Fix failures; don't skip or bypass hooks (`--no-verify` is not allowed).

| Changed | Run |
| --- | --- |
| Any TS/HTML/SCSS/JSON | `pnpm format:check` and `pnpm nx affected -t lint typecheck test build --base=origin/main` |
| `libs/shared/contracts` | the row above; it must build in both `web` and `backend` |
| `apps/web` UI or an API flow | also `pnpm nx e2e web-e2e` |
| Python | `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy libs/py-core/src services/ai-api/src services/ingestion-worker/src eval/src`, `uv run lint-imports`, `uv run pytest -m "not integration" -q` |
| `apps/backend/prisma/schema.prisma` | a migration exists in `apps/backend/prisma/migrations`, and `pnpm db:drift` is clean (needs `DATABASE_URL`) |
| Retrieval, chunking or prompts | `make eval-validate`; put the eval results in the PR |
| Dockerfiles / compose / CI | `docker compose -f infra/docker/docker-compose.yml config -q` (YAML) |

`make check` runs all fast gates. Write down the commands you ran and their results: they go in the PR's "How it was tested" section.

## 4. Commit

Format (the full guide is in `.gitmessage`; the `commit-msg` hook enforces it):

```
<type>(<scope>): <summary>

<body: why, wrapped at 72>

<footer: Refs/Closes #n, BREAKING CHANGE: ...>
```

- types: `feat fix perf refactor test docs build ci chore revert`
- scopes (optional): `web backend ai-api worker core contracts db eval infra ci deps docs m0`
- Summary: imperative, lowercase start, no trailing period, 72 characters or fewer.
- Commit with `git commit -F <file>` or several `-m` flags. If a hook rewrites files (prettier, ruff, whitespace), re-stage them and make a **new** commit attempt. Don't amend someone else's commit.

## 5. Push and open the PR

- `git push -u origin <branch>`. The pre-push hook runs nx affected, mypy, import-linter and pytest.
- PR title = the squash commit that lands on `main`, so it follows the same `type(scope): summary` rule (CI: `PR hygiene / Conventional Commit PR title`).
- Body: copy `.github/pull_request_template.md` and fill in **every** section. Tick only the boxes that are true. Write "none" or "n/a" instead of deleting a required section; delete Screenshots only when there's no UI change.
- **Trunk-based: every PR targets `main`.** Never open a PR into another feature branch (no stacked PRs). If the work depends on an unmerged PR, ask the user whether to wait for it, add the work to that PR's branch, or rebase onto `main` after it merges.
- `gh pr create --base main --title "<title>" --body-file <filled-template>`; add `--draft` if any gate is still red or work remains. PRs are squash-merged.
- Share the PR URL with the user, with a short summary of the checks that ran and anything left open.
