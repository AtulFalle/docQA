# 0004. Data residency

- Status: Proposed. Decision needed before M2, and before any real customer document is ingested.

## Context

Ingested documents can contain personal data and confidential business information. Where they are stored, where they are processed (including by third-party LLM and embedding APIs), and how long they are kept are compliance questions. They also shape the deployment design (ADR 0002) and the provider choice (ADR 0003). Tenant isolation inside the database (row-level security) is already designed; this ADR covers geography and retention.

## Options

1. **Single region per deployment.** All data for all tenants lives in one region, chosen at deployment time. Simple to operate and audit.
   - Cons: one region may not satisfy every customer's residency rule.
2. **Region per deployment, tenants placed by deployment.** The same code runs in several regions (for example EU and US). A tenant's data never leaves the region it was placed in.
   - Pros: meets residency rules without per-tenant branching in code.
   - Cons: separate databases, indexes and Temporal namespaces per region; more to operate.
3. **Per-tenant region pinning inside shared infrastructure.** Tenant rows carry a region; storage and processing are routed by region.
   - Cons: highest complexity; routing errors become data-residency incidents.
4. **Self-hosted processing only.** Keep embedding and generation models inside the chosen region (see ADR 0003, option 3).

## Recommended default

Option 1 for the first environment: a single region, recorded in the deployment config, with all processing (including any third-party model calls) inside that region's provider endpoints where the provider offers them. Option 2 is the likely next step if a second region is required. Do not build per-tenant routing (option 3) until a customer requires it.

## Open questions

- Which regions must be supported at launch, and which regulations apply (for example GDPR, or sector rules)?
- Are third-party model APIs acceptable for all document classes, or must some tenants use self-hosted models?
- What are the retention periods for raw uploads, extracted text, chunks, embeddings, query logs and LLM traces (Langfuse, OTel)?
- Who may access raw documents for support or debugging, and is that access logged in `audit_log`?
- Are deletion requests expected to remove data from Qdrant, object storage and traces within a fixed time?

## Consequences

Every stored artefact needs a clear location and retention rule before go-live. Logs and traces must not carry document text by default, because they are kept in separate stores with their own retention. The retention and deletion answers feed the Temporal `delete` workflow design (M1).
