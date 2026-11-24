# 0003. LLM and embedding provider

- Status: Proposed. Decision needed before M1 (answer generation) and M2 (embedding and indexing).

## Context

Two model roles are needed. A **generation** model writes grounded answers with citations from retrieved chunks. An **embedding** model turns chunks and queries into vectors for Qdrant. The choice affects answer quality, cost per query, latency, data handling (see ADR 0004), and how easily the provider can be replaced. The `ANTHROPIC_API_KEY` placeholder in `.env.example` is reserved for the generation role and is not used until M1.

## Options

For generation:

1. **Anthropic Claude API** through the official SDK. Hosted, strong at long-context grounded answers, and the project already has an API key placeholder for it.
2. **Another hosted LLM API** (for example OpenAI or a cloud-hosted model service). Comparable choice; would need the same evaluation on the golden set.
3. **Self-hosted open-weights model** on our own GPUs. Best residency control; higher operating cost and a quality gap that must be measured.

For embeddings:

1. **Hosted embedding API** (for example Voyage AI, which Anthropic recommends for embeddings, or an OpenAI embedding model). Simple to run; document text leaves our infrastructure.
2. **Self-hosted open embedding model** behind a text-embeddings service. No text leaves our infrastructure; we run and upgrade the model ourselves.

## Recommended default

- Generation: Anthropic Claude API, behind a small provider interface in `docqa_core` so that a second provider can be added without touching the pipeline.
- Embeddings: decide after the M0 golden set exists. Measure recall@k for a hosted and a self-hosted model on the same corpus. Until then, the interface must record the embedding model name and version on every chunk (`chunks.embedding_model`, `chunks.index_version`), so that re-embedding is possible later.

## Open questions

- Is sending document excerpts to a third-party API allowed for every tenant? (Links to ADR 0004.)
- What is the monthly budget for generation and embedding, and at what query volume?
- What answer-quality threshold (from the golden set) must the chosen model meet before M1 exits?
- Are there contractual requirements on retention or training use with the provider?
- Is a self-hosted model in scope for the first production release, or only as a fallback?

## Consequences

The pipeline depends on an interface, not a vendor. Every embedding is tied to a model name and an index version, so changing models means a reindex job rather than a schema change. Eval runs must be repeated after any provider change, and the results recorded in the milestone file.
