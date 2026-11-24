## Summary

<!-- What does this PR change, and why? Link the issue or ADR if there is one. -->

## Milestone

<!-- e.g. M0, M1. Delete the other options. -->
- [ ] M0
- [ ] M1
- [ ] M2
- [ ] Other / no milestone

## Checklist

- [ ] Tests added or updated (unit, and integration where it touches Postgres, Temporal or Qdrant)
- [ ] `uv run ruff check .`, `uv run ruff format --check .` and `uv run mypy` pass locally
- [ ] Eval impact considered: golden set or metrics changed, or "no retrieval or answer change"
- [ ] Migration: none, or added as a Prisma migration (apps/backend/prisma/migrations), zero-downtime safe
- [ ] Security / ACL impact considered: tenant isolation (RLS), document permissions, logging of sensitive content
- [ ] Docs updated (README, ADR, or milestone checklist) where behaviour or setup changed
