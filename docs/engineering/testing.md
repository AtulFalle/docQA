# Testing standards

## Pyramid

- Many fast **unit** tests (pure logic, services with fakes, no network, no DB). Fewer **integration** tests (real Postgres, Temporal dev server) marked `@pytest.mark.integration`. A few **eval/e2e** checks (golden set). **[Review]**
- Markers are strict: unknown markers fail. **[Enforced: pytest `--strict-markers`]**
- `uv run pytest -m "not integration"` must pass with zero infrastructure and finish in seconds.

## Naming and layout

- Tests live in `<pkg>/tests/`. Files are `test_<pkg>_<topic>.py` and **file names are unique across the repo** (`test_core_rls.py`, `test_ai_api_health.py`), avoiding module-name collisions. **[Review; pytest rootdir import errors surface it]**
- Functions: `test_<unit>_<behaviour>`, e.g. `test_chunker_splits_on_heading_boundary`. One behaviour per test.
- Tests are exempt from docstrings, magic-number, private-access and security lint rules. **[Enforced: ruff per-file-ignores]**

## Structure

- Arrange / Act / Assert, separated by blank lines. Assert on outcomes, not implementation calls.
- Fixtures over setup code; shared ones in `conftest.py`, narrowest scope that works. Use `tmp_path`, `monkeypatch`, `caplog`/log capture, not globals.
- Parametrise (`pytest.mark.parametrize`) instead of loops. **[Enforced: ruff PT]**
- `asyncio_mode = "auto"`: write `async def test_...` with no decorator.
- Use builders/factories for test data; no giant JSON blobs inline.

```python
# bad
def test_1():
    ...
    time.sleep(2)
    assert x


# good
async def test_ingest_workflow_marks_job_failed_after_retries(time_skipping_env):
    result = await run_workflow(time_skipping_env, failing_activity)
    assert result.status is JobStatus.FAILED
```

## Isolation rules

- No real network in unit tests; mock LLMs, embedders, HTTP (`httpx.MockTransport`). Deterministic tests only. **[Review]**
- No `sleep`: use time-skipping Temporal env, fake clocks, or events. **[Review]**
- No test depends on order or on state left by another test; integration tests use per-test transactions or unique tenant ids.
- `xfail_strict = true`: an unexpectedly passing xfail fails. **[Enforced: pytest]**

## Security-critical tests

For every new tenant-scoped feature: **[Review]**

- A test where tenant A cannot read, list, update or delete tenant B's data (API and DB level).
- A test where a user without ACL access never sees the document in search results, citations or error text.
- A test that a new table has RLS (existing `test_core_rls` / `test_core_models` cover table registration).
- Negative tests for malformed/oversized input.

## Retrieval and RAG changes

- Any change to chunking, embeddings, retrieval, reranking or prompts includes golden-set results in the PR (`rag-and-llm.md`). Unit tests assert plumbing; the eval set asserts quality.
- New failure found in production or review becomes a golden-set item or a regression test.

## Coverage

- Branch coverage is on; floor is `fail_under` in `[tool.coverage.report]`. **[Enforced: pytest-cov / coverage]**
- **Ratchet**: when coverage rises, raise `fail_under` (round down to the nearest 1-2 points). Lowering needs an ADR. **[Review]**
- New code should be covered by its own PR; do not rely on the global floor. Critical paths (auth, ACL, RLS, ingestion idempotency) aim for near 100% branches.
- Do not game it: no assertion-free tests, no `# pragma: no cover` without a reason.

## Flaky tests

- A test that fails intermittently is a bug. Within **24 hours** of the first flake: open a ticket, mark `@pytest.mark.skip(reason="flaky: #123")` (quarantine) or fix it, and keep main green. **[Review]**
- Quarantined tests have an owner and are fixed or deleted within two weeks. Never "retry until green" in CI.
