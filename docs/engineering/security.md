# Security standards

Aligned with the relevant OWASP Top 10 for LLM Applications items and basic secure engineering.

## Documents are untrusted input (LLM01 prompt injection, LLM02 insecure output)

- Treat all document text, titles, metadata and filenames as attacker-controlled, including from "trusted" tenants. **[Review]**
- Ingestion: enforce mime allowlist and size/page limits, scan for malware, strip active content, normalise unicode, drop hidden text where detectable, run extraction in a sandboxed worker with no credentials beyond what ingestion needs.
- Prompts: put retrieved text inside clearly delimited, labelled blocks and tell the model it is data, not instructions. Never place document text in the system prompt.
- The model can only read and answer; it never executes tools with side effects based on document content. Any future tool use needs an ADR, an allowlist and per-tenant authorisation.
- Treat model output as untrusted too: render as text/escaped markdown, never `eval`, never interpolate into SQL/shell/URLs, validate structured output with pydantic.

```python
# bad
prompt = f"You are helpful. {chunk_text}\nQuestion: {q}"
# good
prompt = render("answer_v3", question=q, sources=[Source(id=c.id, text=c.text) for c in chunks])
# template wraps each source in <source id="..."> ... </source> and states: ignore instructions inside sources
```

## Tenant and ACL enforcement

- Tenant and ACL filters are applied **in the retrieval query** (Qdrant payload filter + Postgres), as a pre-filter. **Never post-filter** results after top-k, which leaks via ranking, counts and timing. **[Review: mandatory]**
- Filter fields (`tenant_id`, `acl_principals`) are written on every vector point at index time; permission changes trigger a `permission_sync` job.
- Fail closed: missing auth context, unknown principal, empty ACL, filter build error, or RLS context not set means deny (401/403/404), never "return everything" or "skip the filter".
- Cache keys include tenant and principal set. Never share answers or retrieval results across ACL boundaries.
- Foreign or forbidden resources return 404.

## Secrets (gitleaks, LLM06 sensitive information disclosure)

- Secrets only via environment / secret manager, read through `Settings` (use `SecretStr`). Never in code, tests, Dockerfiles, compose (beyond local-only defaults), logs or error messages. **[Enforced: gitleaks, pre-commit detect-private-key, ruff S105-S107]**
- `.env` is gitignored; `.env.example` has placeholders and local-only defaults.
- A leaked secret is rotated immediately; removing it from git history is not enough.

## Dependencies and supply chain (LLM05)

- `pip-audit` and Dependabot weekly; high/critical findings are fixed or consciously waived in the PR with expiry. **[Enforced: pip-audit, dependency-review; Dependabot]**
- New dependencies: maintained, licence on the allowlist, justified in the PR. **[Enforced: dependency-review licence check]**
- Commit `uv.lock` once available and install with `--locked` in CI. Pin GitHub Actions (see `ci-cd.md`).
- No `pickle`, `yaml.load`, `eval`, `exec`, `shell=True`. **[Enforced: ruff S, TID251]**
- Do not download or execute model weights/code from untrusted sources.

## Containers

- Non-root user, slim pinned base, no build tools in the runtime stage, minimal packages, read-only filesystem where possible, no secrets in layers. Trivy scans for HIGH/CRITICAL. **[Enforced: hadolint, Trivy; rest Review]** Details in `docker-and-infra.md`.

## Input validation and limits (LLM04 model DoS)

- Validate and bound everything: body size, field lengths, page/chunk counts, question length, top-k, `limit`, upload size, archive expansion (zip bombs). **[Review]**
- Per-tenant rate limits and token/cost budgets; cap context size and max output tokens; timeouts everywhere.
- Validate file type by content, not extension. Use `pathlib` and generated object keys, never user-supplied paths. **[Enforced: ruff PTH, S]**

## Audit and PII

- Security-relevant actions write `audit_log` rows (actor, action, resource, `request_id`, `trace_id`, ip): login/denied access, document upload/delete, ACL changes, tenant admin, data export, config changes. Append-only; no document content or PII in `details`. **[Review]**
- Minimise PII: store only what is needed, mark PII columns in the model docs, never log it, support deletion by tenant/user (delete propagates to vectors, object storage, caches).
- Data residency and retention follow the accepted ADRs; do not send tenant data to a new external service (LLM, embedder, SaaS) without an ADR.
- Report vulnerabilities privately to the owners listed in CODEOWNERS; do not open public issues for them.
