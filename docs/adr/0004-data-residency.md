# 0004. Data residency

- Status: Accepted
- Date: 2026-11-28

The processing rule and the placement model are decided. The specific region and the retention values are still open (see Open questions) and must be confirmed before any real customer document is ingested.

## Context

Ingested documents can contain personal data and confidential business information. Where they are stored, where they are processed (including by LLM and embedding models), and how long they are kept are compliance questions. They also shape the deployment design (ADR 0002) and the provider choice (ADR 0003). Tenant isolation inside the database (row-level security) is already designed; this ADR covers where data goes and how long it stays.

## Options considered

1. **Single region per deployment.** All data for all tenants lives in one region, chosen at deployment time. Simple to operate and audit.
   - Cons: one region may not satisfy every customer's residency rule.
2. **Region per deployment, tenants placed by deployment.** The same code runs in several regions (for example EU and US). A tenant's data never leaves the region it was placed in.
   - Pros: meets residency rules without per-tenant branching in code.
   - Cons: separate databases, indexes and Temporal namespaces per region; more to operate.
3. **Per-tenant region pinning inside shared infrastructure.** Tenant rows carry a region; storage and processing are routed by region.
   - Cons: highest complexity; routing errors become data-residency incidents.
4. **Self-hosted processing only.** Keep embedding and generation models inside our own infrastructure (see ADR 0003).

## Decision

- **Option 4: self-hosted processing only.** No document content, question text, chunk or embedding is sent to a third-party API. That covers raw files, extracted text, prompts, answers and traces. Parsing, OCR, embedding, reranking and generation all run inside our infrastructure (ADR 0003).
- **Option 1 for placement:** one region per deployment, recorded in the deployment config. Option 2 is the next step if a second region is required. Per-tenant routing (option 3) is not built until a customer requires it.
- Logs, traces (OpenTelemetry, Langfuse) and analytics events must not carry document text by default, because they live in separate stores with their own retention.

## Open questions

These must be answered before real customer documents are ingested:

- Which region or regions must be supported at launch, and which regulations apply (for example GDPR or sector rules)?
- Are the retention defaults in ADR 0006 §9 right for raw uploads, extracted text, chunks, embeddings, query logs and LLM traces?
- Who may access raw documents for support or debugging, and how is that access logged in `audit_log`?
- What is the deadline for removing deleted data from Qdrant, object storage and traces?

## Consequences

- No hosted model API can be used for document content, in any environment that holds real data. Hosted APIs are allowed only with synthetic test data, if at all.
- Every stored artefact needs a clear location and retention rule before go-live.
- The retention and deletion answers feed the Temporal `delete` and `purge` workflows (ADR 0006 §4.4).
