# Python standards

Python 3.12, `ruff` + `mypy --strict`. Rationale for the rule families lives here; thresholds live in `pyproject.toml`.

## Style and naming

- 100-column lines, double quotes, formatted by `ruff format`. **[Enforced: ruff format, E/W]**
- `snake_case` functions/modules, `PascalCase` classes, `UPPER_CASE` constants, no shadowed builtins. **[Enforced: ruff N, A]**
- Use modern syntax: `X | None`, `list[int]`, `StrEnum`, `pathlib`. **[Enforced: ruff UP, PTH]**
- Timezone-aware datetimes only: `datetime.now(UTC)`. **[Enforced: ruff DTZ]**
- No `print`, no leftover debuggers, no commented-out code. **[Enforced: ruff T20, T10, ERA]**
- Boolean parameters are keyword-only. **[Enforced: ruff FBT]**

```python
# bad
def search(q, tenant, True): ...
# good
def search(query: str, tenant_id: UUID, *, rerank: bool = True) -> list[Hit]: ...
```

## Typing

- `mypy --strict`, plus `warn_unreachable` and `ignore-without-code`. **[Enforced: mypy]**
- Pydantic models at boundaries (HTTP, config, queue/workflow payloads, LLM structured output). Dataclasses (`frozen=True, slots=True`) or `TypedDict` for internal data. **[Review]**
- No `Any` in public signatures. If you must accept untyped data, take `object` or a `TypedDict`/pydantic model and validate it. **[Review]**
- Parse, do not validate-and-pass-around: convert raw dicts to typed objects at the edge.
- Use `StrEnum` for closed sets, `NewType` for easily confused IDs when it prevents real bugs.

## Size and complexity

Numbers mirror `[tool.ruff.lint]`: **[Enforced: ruff C901, PLR]**

| Limit | Value |
|-------|-------|
| McCabe complexity | 10 |
| Arguments | 6 |
| Branches | 12 |
| Returns | 6 |
| Statements | 50 |
| Nested blocks | 4 |
| Module length | 400 non-blank lines **[Enforced: `tools/check_file_length.py`, pre-commit + CI]** |

Hitting a limit means split the function, not raise the limit. Guard clauses beat nesting.

## Error handling

- Define domain exceptions in `docqa_core.domain.errors` (`class DocumentNotFoundError(NotFoundError)`); each has a stable `code` and a `retryable` flag; raise them from services; translate at the edge (HTTP handler, Temporal error type). **[Review]**
- No bare `except:` or blind `except Exception:` unless you log with context and re-raise. **[Enforced: ruff BLE, TRY]**
- Never swallow: no `except ...: pass`. Use `contextlib.suppress` only for a specific, expected exception. **[Enforced: ruff SIM105, S110]**
- Raise from the cause: `raise IngestError(doc_id) from exc`. **[Enforced: ruff B904]**

```python
# bad
try:
    await store.put(key, data)
except Exception:
    pass
# good
try:
    await store.put(key, data)
except StorageUnavailable as exc:
    log.warning("storage.put.failed", key=key, error=str(exc))
    raise
```

## Async

- No blocking I/O in `async def` (`time.sleep`, `open`, sync DB/HTTP). Use `asyncio.sleep`, `anyio`/`asyncio.to_thread` for unavoidable blocking calls. **[Enforced: ruff ASYNC]**
- Every network call has an explicit timeout (httpx `Timeout`, DB `statement_timeout`, Temporal activity timeouts). **[Review]**
- `httpx.AsyncClient`, never `requests`; share one client per process, close it in lifespan. **[Enforced: ruff TID251]**
- Do not fire-and-forget tasks without holding a reference and handling errors. Prefer `asyncio.TaskGroup`. **[Enforced: ruff RUF006]**

## Configuration

- All configuration comes from `docqa_core.config.Settings` (`DOCQA_*` env vars). `os.getenv` and `os.environ` are banned outside `config.py`. **[Enforced: ruff TID251]**
- New setting: add a typed field with a safe default or no default for secrets, and a line in `.env.example`.
- Pass `Settings` (or the slice you need) in; never import a global.

## Logging

- Use `docqa_core.logging.get_logger(__name__)`; `logging.getLogger` is banned. **[Enforced: ruff TID251]**
- Event-style names, `component.noun.verb`, and key-value fields. No f-strings or `%` formatting in the event. **[Enforced: ruff G, LOG; naming Review]**

```python
# bad
log.info(f"Chunked doc {doc_id} into {n} chunks")
# good
log.info("ingest.chunk.completed", doc_id=str(doc_id), chunk_count=n, duration_ms=ms)
```

- Never log secrets, PII or document text. See `observability.md`.

## Docstrings

- Google style on public modules' classes/functions/methods; first line is a imperative summary. Private helpers and tests are exempt. **[Enforced: ruff D, convention=google]**
- Document `Raises:` for domain exceptions the caller must handle. **[Review]**

## Module layout

```
libs/py-core/src/docqa_core/   config, logging, telemetry, value_sets, domain/ (types, errors), db/ (models, session)
services/ai-api/src/docqa_ai_api/          main, middleware, routes/, (services/, schemas/)
services/ingestion-worker/src/docqa_workers   workflows/, activities/, worker.py
eval/src/docqa_eval/        schema, dataset, metrics, cli
```

- Absolute imports only: `from docqa_core.db import Base`. **[Enforced: ruff TID252]**
- No `import *`; define `__all__` in package `__init__` re-exports. **[Enforced: ruff F403, RUF022]**
- Lazy imports are allowed for optional deps only; keep them rare. **[Review]**
- Banned: `pickle`, `sqlalchemy.orm.Session` (use `AsyncSession`). **[Enforced: ruff TID251]**

## Dependency rules (import-linter)

Contracts in `[tool.importlinter]`: **[Enforced: lint-imports]**

1. `docqa_core` is a leaf: it never imports `docqa_ai_api`, `docqa_workers`, `docqa_eval`. Shared code goes down into core, never sideways.
2. Core stays framework-agnostic: no `fastapi`, `starlette`, `uvicorn`, `temporalio`. Keeps it reusable and cheap to test.
3. `docqa_ai_api`, `docqa_workers`, `docqa_eval` are independent of each other. Need to share? Move it to core.
4. `docqa_eval` is standalone: no `docqa_core`, `sqlalchemy`, `fastapi`, `temporalio`. It must run on a laptop with only pydantic, and talks to the system via public APIs.

Adding a third-party dependency: add it to the package's `pyproject.toml` that imports it (deptry checks this), pin a lower bound, and justify anything heavy in the PR. **[Enforced: deptry]**
