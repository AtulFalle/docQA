# Temporal standards

Ingestion runs as Temporal workflows (`docqa_workers.workflows`) calling activities (`docqa_workers.activities`). Workflows orchestrate; activities do the work.

## Workflow determinism

A workflow is replayed from history, so it must make the same decisions every time. **[Review; replay tests catch regressions]**

- No I/O in workflow code: no DB, HTTP, filesystem, env, Settings reads.
- No wall clock, randomness or ids: use `workflow.now()`, `workflow.random()`, `workflow.uuid4()`; never `datetime.now()`, `random`, `uuid.uuid4()`, `time.time()`.
- No threads, no `asyncio.sleep` (use `workflow.sleep`), no iteration over unordered sets/dicts for decisions.
- Import activities and heavy modules inside `workflow.unsafe.imports_passed_through()` as in `workflows/ingest.py`.
- Keep workflows small: a loop over stages with timeouts and retry policy. Business logic lives in activities or core.

```python
# bad
started = datetime.now(UTC)
doc_key = str(uuid.uuid4())
# good
started = workflow.now()
doc_key = str(workflow.uuid4())
```

## Activities

- **Idempotent**: a retry or duplicate delivery must produce the same end state. Derive keys from content, not attempt: `chunk_id = sha256(doc_version_id + chunk_index + text_hash)`; use upserts keyed by content hash for vector points and DB rows. **[Review]**
- Check "already done?" before expensive work (embedding calls cost money).
- Activities never assume the previous activity ran on the same worker or disk. Hand off via object storage / DB, not local files.
- Set tenant context and enforce tenant/ACL fields on every write (see `database.md`, `security.md`).

## Inputs and outputs

- Small, serialisable dataclasses or pydantic models. Pass **IDs, not payloads**: `IngestInput(tenant_id, document_id, document_version_id)`, never document text, embeddings, or file bytes. Temporal history has size limits and is stored, replayed and visible in the UI. **[Review]**
- Add fields with defaults only; never rename or remove fields of in-flight payloads (see versioning).
- Do not put secrets or document content in workflow inputs, memos, search attributes or error messages.

## Timeouts and retries

- Every `execute_activity` sets `start_to_close_timeout` explicitly (and `schedule_to_close_timeout` when queue wait matters). No unbounded activities. **[Review]**
- Every activity gets a `RetryPolicy`: bounded `maximum_attempts`, exponential backoff, `maximum_interval`. Do not retry forever by default.
- Declare non-retryable errors: bad input, validation failure, permission denied, unsupported mime type (`non_retryable_error_types=["ValidationError"]`). Raise `ApplicationError(..., non_retryable=True)` for permanent failures. Transient errors (timeouts, 429, 5xx) retry.
- Poison documents must end in `failed` status with a reason code, not loop.
- Compensate on failure (mark job and document status) in a `try/except` in the workflow, using an activity.

## Heartbeats

- Activities longer than ~30s (OCR, big PDFs, bulk embedding) call `activity.heartbeat(progress)` regularly and set `heartbeat_timeout`, so a dead worker is detected fast and retried from last progress.
- Handle cancellation (`asyncio.CancelledError`) to release resources.

## Versioning

- Changing workflow code that in-flight executions already ran breaks replay. Gate changes with `workflow.patched("ingest-add-ocr-v1")`, later `deprecate_patch`, or use a new workflow type/task queue for incompatible changes. **[Review]**
- Never reorder, remove or rename activities or change their timeouts in an existing path without a patch.
- Add a replay test for each released workflow shape (`Replayer` over saved histories) when versioning logic is introduced.

## Testing

- Use `WorkflowEnvironment.start_time_skipping()` so retries and timeouts run instantly; never `sleep`. **[Review]**
- Unit test activities as plain async functions with fakes for DB/LLM/vector store.
- Workflow tests register fake activities with the same names (`@activity.defn(name=...)`) to assert ordering, retry and failure paths.
- Tests needing a real Temporal dev server are `@pytest.mark.integration`.
- Test names: `test_workers_<behaviour>.py` (unique names, see `testing.md`).
