# FastAPI standards

## Structure

- Routes are thin: parse input, call a service function, map the result to a response model. No SQL, no business rules, no LLM calls in route functions. **[Review]**
- Services live in `docqa_ai_api.services`, take explicit dependencies (session, settings, clients), and return domain objects or pydantic models. They are unit-testable without HTTP. **[Review]**
- All public routes live under `/v1` (`APIRouter(prefix="/v1")`). Breaking change means `/v2`, not editing `/v1`. Health endpoints (`/healthz`, `/readyz`) stay unversioned. **[Review]**

```python
# bad: logic in the route
@router.post("/documents")
async def create(req: Request):
    body = await req.json()
    ...  # 80 lines of SQL and rules


# good
@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
async def create_document(
    body: DocumentCreate,
    ctx: Annotated[AuthContext, Depends(require_auth)],
    svc: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentOut:
    return await svc.create(ctx, body)
```

## Schemas

- Request and response bodies are pydantic models with `model_config = ConfigDict(extra="forbid")` on requests (unknown fields are a 422, not silently ignored). **[Review]**
- Never return ORM objects or `dict[str, Any]`; declare `response_model` and an explicit `status_code` on every route. **[Review; mypy catches missing return types]**
- Separate `XCreate`, `XUpdate`, `XOut` models. Do not reuse DB models as API schemas.
- Constrain input: `Field(max_length=...)`, `conint`, enums, list size limits, request body size cap in middleware.

## Dependency injection

- Settings, DB session, auth context and clients come from `Depends(...)` (or `app.state` set in lifespan). No module-level globals or `os.getenv`. **[Enforced: ruff TID251 for env; rest Review]**
- Tests override dependencies via `app.dependency_overrides`.
- One `AsyncSession` per request via a dependency that yields, commits on success, rolls back on error. See `database.md`.

## Auth and tenancy

- **Never trust `tenant_id` (or user id, roles) from the request body, path or query.** Derive them from the verified auth token into `AuthContext`; then call `set_tenant_context` before any query. **[Review: mandatory checklist item]**
- Authorise every object access against the document ACL, not only the tenant. Missing or foreign object returns 404, not 403, to avoid existence leaks.
- Request schemas must not have a `tenant_id` field. A test per route asserts cross-tenant access is denied.

## Errors

One envelope for every error, produced by exception handlers (domain exception to status code):

```json
{"error": {"code": "document_not_found", "message": "Document not found", "request_id": "..."}}
```

- `code` is stable and machine-readable; `message` is safe for clients (no stack traces, SQL, internal hosts).
- 4xx for caller faults, 502/503/504 for upstream failures, 500 only for bugs (logged with `request_id`). Validation errors use 422 in the same envelope.
- Every response carries `X-Request-ID` (middleware already sets it); log and span it.

## Pagination and filtering

- List endpoints are paginated by default. Use cursor (keyset) pagination: `?limit=50&cursor=...`, max `limit` 200, response `{"items": [...], "next_cursor": "..."|null}`. No unbounded lists, no `OFFSET` on large tables. **[Review]**
- Sort must be deterministic (include a unique tiebreaker such as `id`).

## Idempotency

- Any POST that starts work (ingest, reindex, delete job) accepts an `Idempotency-Key` header. Store key + request hash per tenant; a replay returns the original response, a same-key different-body request returns 409. **[Review]**
- Workflow ids derive from the idempotency key or content hash so a retry cannot start duplicate workflows.
- Long operations return `202 Accepted` with a job id and `GET /v1/jobs/{id}`; do not hold the request open.

## Streaming (SSE)

- Use `StreamingResponse` with `text/event-stream`; send typed events (`token`, `citation`, `done`, `error`) as JSON in `data:`.
- Authorise and set tenant context before the first byte; errors after streaming starts are sent as an `error` event, then close.
- Send periodic keep-alive comments; honour client disconnect (cancel the LLM call, stop spending tokens).
- Do not hold a DB transaction open while streaming; read what you need first, then release the session.
- Citations are emitted with or before the final `done` event (see `rag-and-llm.md`).

## Operational

- Timeouts on every outbound call; rate limit per tenant (Redis). `/readyz` checks dependencies, `/healthz` does not.
- OpenAPI is the contract: keep it accurate (`summary`, `responses`, tags); breaking changes are flagged in the PR. **[Review]**
