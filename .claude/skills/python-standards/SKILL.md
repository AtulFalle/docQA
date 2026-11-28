---
name: python-standards
description: How to write Python in docQA (libs/py-core, services/ai-api, services/ingestion-worker, eval). Covers strict typing, size and complexity limits, module layout and import boundaries, FastAPI routes and pydantic schemas, Temporal workflows, errors, logging and pytest. Use whenever you create or change Python code, pyproject files or Python tests in this repo.
---

# Python standards

Full rules: `docs/engineering/python.md`, `fastapi.md`, `temporal.md`, `testing.md` and `rag-and-llm.md`. **[Lint]** means ruff, mypy, import-linter or the file-length check fails the build.

## Hard limits

| Rule | Limit |
| --- | --- |
| Module size | ≤ 400 non-blank lines **[Lint: tools/check_file_length.py]** |
| Function | ≤ 50 statements, complexity ≤ 10, ≤ 12 branches, ≤ 6 returns, ≤ 6 args, nesting ≤ 4 **[Lint: ruff C901/PLR]** |
| Types | `mypy --strict`: every function fully annotated, no bare `Any`, no untyped defs **[Lint]** |
| Style | ruff (pyflakes, bugbear, bandit, pydocstyle, …), line length 100 **[Lint]** |

Near a limit? Split into smaller functions or modules and use guard clauses instead of nesting. Never raise a limit; every `# noqa: CODE` or `# type: ignore[code]` needs a reason on the same line.

## Code shape

```python
async def ingest_document(doc_id: UUID, *, tenant_id: UUID, force: bool = False) -> IngestResult:
    """Ingest one document for a tenant. Raises DocumentNotFoundError if it doesn't exist."""
    document = await repo.get(doc_id, tenant_id=tenant_id)
    if document is None:
        raise DocumentNotFoundError(doc_id)
    return await _run_pipeline(document, force=force)
```

- Python 3.12 syntax: `list[str]`, `X | None`, `type` aliases, `StrEnum`, `datetime.now(UTC)` (no naive datetimes).
- Boolean options are keyword-only (`*, force: bool`) **[Lint: FBT]**. Use `pathlib` over `os.path`, and no `print` (use the structlog logger).
- Public functions and classes get a one-line docstring (pydocstyle) **[Lint]**.
- Settings come only from `docqa_core.config.get_settings()`; secrets are `SecretStr`.

## Layout and boundaries

- `libs/py-core` (`docqa_core`): config, logging, telemetry, db models, framework-free domain types and errors (`docqa_core.domain`), and the `StrEnum`s shared with TS in `docqa_core.value_sets` (keep them identical to `@docqa/contracts`).
- `services/ai-api` (`docqa_ai_api`): FastAPI app. `routes/` stays thin; add `schemas/` (pydantic) and `services/` (logic) as the first real endpoints land.
- `services/ingestion-worker` (`docqa_workers`): Temporal `workflows/` (deterministic: no I/O, clocks or randomness) and `activities/` (all I/O, idempotent).
- Services and eval never import each other **[Lint: import-linter]**. Declare every import as a dependency in that package's `pyproject.toml` **[deptry]**.

## FastAPI and data

- Routes parse, call a service and return a pydantic response model. Request models use `ConfigDict(extra="forbid")` (unknown fields return 422) and bounded fields (`max_length`, list limits).
- Errors: raise domain exceptions and map them to the error envelope in one handler. No blind `except Exception` **[Lint: BLE]**. An empty `except` must use `contextlib.suppress` plus a reason.
- Every DB query is tenant-scoped (RLS context). Vector search always filters by tenant and ACL.

## Tests

- pytest, `tests/` per package, named `test_<behaviour>`. Mark tests that need Postgres, Temporal or Qdrant with `@pytest.mark.integration`.
- No network in unit tests; inject fakes. Coverage `fail_under` is a ratchet: raise it, never lower it.

## Before you finish

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy libs/py-core/src services/ai-api/src services/ingestion-worker/src eval/src
uv run lint-imports
uv run python tools/check_file_length.py
uv run pytest -m "not integration" -q
```
