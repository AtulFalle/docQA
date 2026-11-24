# Database standards

PostgreSQL 16, Prisma (owned by the NestJS backend) for schema and migrations; SQLAlchemy 2.0 async + psycopg 3 as a read/write mirror in the Python AI services. Tenant isolation uses RLS keyed on `app.tenant_id`.

## Models and sessions

Prisma (`apps/backend/prisma`) is the source of truth for the schema. The SQLAlchemy models in `docqa_core.db` are a mirror: change the Prisma schema and migration first, then update the mirror. **[Enforced: `test_core_schema_contract`]**

- Typed declarative models: `Mapped[...]` + `mapped_column(...)`. No legacy `Column()` style. **[Enforced: mypy strict]**
- `AsyncSession` only. `sqlalchemy.orm.Session` is banned. **[Enforced: ruff TID251]**
- Every model inherits `Base` (naming convention is set there: `ix_`, `uq_`, `fk_`, `pk_`, `ck_`). Never pass hand-written constraint names that contradict it. **[Review]**
- Use `TimestampMixin` for `created_at`/`updated_at`; timestamps are `timestamptz`, UTC.
- Closed sets are `StrEnum` stored as `native_enum=False` (see `_enum` helper): adding a value needs no `ALTER TYPE`.
- One transaction per request / unit of work, opened and committed at the edge (request dependency, Temporal activity), not inside repositories. Services never call `commit()` mid-flow. **[Review]**

## Tenant context (critical)

- Call `set_tenant_context(session, tenant_id)` before any tenant-scoped query, in the same transaction. It uses `set_config(..., true)` so it dies with the transaction. **[Review: mandatory checklist item]**
- RLS is defense-in-depth, not the filter. Queries still say `WHERE tenant_id = :tenant_id` so plans use the index and a missing policy cannot leak data.
- `tenant_id` comes from the auth context, never from client input.

```python
# bad: relies on RLS alone, tenant from request body
rows = await session.scalars(select(Document).where(Document.id == body.document_id))

# good
await set_tenant_context(session, ctx.tenant_id)
rows = await session.scalars(
    select(Document).where(Document.tenant_id == ctx.tenant_id, Document.id == document_id)
)
```

- Every new tenant-scoped table must (a) have a `tenant_id` FK to `tenants.id`, (b) get `ENABLE` + `FORCE ROW LEVEL SECURITY` and the `tenant_isolation` policy in its Prisma migration (raw SQL), and (c) be listed in `TENANT_SCOPED_TABLES`. **[Enforced: `test_core_models`, `test_core_schema_contract` and `test_core_rls` compare metadata, the constant and live policies]**
- Only `tenants` and `audit_log` are exempt. A new exemption needs an ADR.
- The application role must not be a superuser or have `BYPASSRLS`. **[Review]**

## Queries

- Bound parameters only. Never build SQL with f-strings, `%` or `+`. Use SQLAlchemy expressions; if you need `text()`, use `:name` binds. **[Enforced: ruff S608]**
- Avoid N+1: eager-load with `selectinload`/`joinedload` or fetch with one `IN`/join query. In async code lazy loading raises, which is a feature. **[Review]**
- Bound every result set: `limit`, keyset pagination, streaming (`stream_scalars`) for exports.
- Every FK column used in filters or joins has an index; composite indexes start with `tenant_id` (`ix_jobs_tenant_id_status`). Check with `EXPLAIN` for new hot queries. **[Review]**
- Do not hold transactions open across network calls (LLM, vector store, object storage).
- Set `statement_timeout`/`lock_timeout` for application roles; migrations set their own `lock_timeout`.

## Prisma migrations

- Prisma owns the schema. Migrations are SQL files under `apps/backend/prisma/migrations`, one per PR; the folder name and message describe the change. **[Review]**
- Generated SQL is a draft. Hand-review: no accidental drops, correct defaults, index/constraint names follow the convention. **[Review]**
- RLS (`ENABLE` + `FORCE ROW LEVEL SECURITY`, policies) is not expressible in the Prisma schema: write it as raw SQL in the migration. **[Review]**
- Schema and migrations must not drift. **[Enforced: `prisma migrate diff --exit-code` in CI]**
- The Python mirror must match the migrated database. **[Enforced: `libs/py-core/tests/test_core_schema_contract.py`]**
- Migrations are plain DDL plus small data fixes. Rollback is forward-only: ship a new corrective migration.

### Zero-downtime patterns (expand / contract)

Assume old and new app versions run side by side during a deploy.

| Want | Do this |
|------|---------|
| Add column | Nullable (or with constant default), deploy code that writes it, backfill, then add `NOT NULL` via a `CHECK ... NOT VALID` + `VALIDATE` |
| Rename column/table | Never in one step. Add new, dual-write, backfill, switch reads, then drop old in a later release |
| Drop column | Stop reading and writing in code first (release N), drop in release N+1 |
| Add index on big table | `CREATE INDEX CONCURRENTLY` in its own migration ; nothing else in that migration |
| Add FK / constraint | `NOT VALID` first, `VALIDATE CONSTRAINT` separately |
| Backfill | Batched job (Temporal workflow, e.g. 5k rows per transaction), idempotent and resumable; never one giant `UPDATE` in a migration |
| Change type | New column + backfill + swap, not `ALTER COLUMN TYPE` on big tables |

```sql
-- good: concurrent index, own migration (Prisma runs a file with a single statement outside a transaction block)
CREATE INDEX CONCURRENTLY "ix_chunks_tenant_id_document_id" ON "chunks" ("tenant_id", "document_id");
```

- Set `SET lock_timeout = '5s'` at the top of DDL migrations so a blocked lock fails fast instead of queueing the whole app behind it.
- Destructive migrations (drops, truncates) call out the data loss and the backup/rollback plan in the PR.

## Naming

- Tables: plural `snake_case` (`document_versions`). Columns: `snake_case`, FKs `<entity>_id`. Booleans `is_`/`has_`. Timestamps `*_at`.
- Constraint and index names follow the convention in `db/base.py`; keep the Prisma schema (`map:`) consistent with it.
- Migration names: imperative, lower case (`add document_acls table`).
