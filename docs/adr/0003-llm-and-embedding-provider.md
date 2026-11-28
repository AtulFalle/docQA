# 0003. LLM and embedding provider

- Status: Accepted
- Date: 2026-11-28

## Context

Two model roles are needed. A **generation** model writes grounded answers with citations from retrieved chunks. An **embedding** model turns chunks and queries into vectors for Qdrant. A **reranker** reorders the retrieved candidates. The choice affects answer quality, cost per query, latency, data handling (see ADR 0004), and how easily the provider can be replaced.

The planning discussion on 2026-11-28 set the data-handling rule: **no document content may leave our infrastructure**. Every model that sees document text or questions about it falls under that rule. Expected scale is 100k–1M documents in the first 12 months (see Discussion #156).

## Options considered

For generation:

1. **Hosted LLM API** (a commercial model API or a cloud-hosted model service). Strong at long-context grounded answers with no GPUs to run. Rejected: document excerpts would leave our infrastructure.
2. **Self-hosted open-weights model** on our own GPUs. Best data control. Operating cost and the quality gap must be measured on the golden set.

For embeddings and reranking:

1. **Hosted embedding or rerank API.** Rejected: document text leaves our infrastructure.
2. **Self-hosted open models** behind an embeddings service. No text leaves our infrastructure; we run and upgrade the models ourselves.

## Decision

All models are **self-hosted** (generation option 2, embeddings option 2).

- **Serving.** vLLM serves the generation model behind an OpenAI-compatible endpoint, reached through the `openai_compat` provider adapter (Discussion #133). Ollama is allowed for local development on a laptop. Embedding and reranker models are served on our own infrastructure too.
- **Interfaces.** Every model sits behind the `LLMClient`, `Embedder` and `Reranker` interfaces (`docs/engineering/rag-and-llm.md`), so a model or size change is a configuration change.
- **Model and size are chosen by eval, not by leaderboard.** Once vLLM serving (M4) and the answer metrics and eval runner (M6, PR-603 and PR-604) exist, the golden set runs against two or three model sizes. We choose the smallest size that meets the quality thresholds (faithfulness, citation precision and abstention on unanswerable questions). Its hardware becomes the GPU budget request. Rough starting tiers, to be checked against our own data:

  | Tier | Hardware | Fits |
  |---|---|---|
  | Dev | 1× 24 GB GPU | ~8B LLM + small embedding and reranker models |
  | Prod small | 1× 80 GB (or 2× 48 GB) + 1× 24 GB | quantized ~30B LLM; embedding and reranking on the smaller GPU |
  | Prod comfortable | 2–4× 80 GB | 70B-class LLM, or ~30B with more concurrency |

- **The LLM-as-judge** used for faithfulness scoring in eval is self-hosted as well, and pinned by name and version.
- Every embedding still records its model and index version (`search_indexes`, ADR 0006), so changing models means a reindex job rather than a schema change.

## Consequences

- GPUs become the main operating cost and capacity limit. Deployments need GPU nodes (see ADR 0002).
- Open models usually cite and stay faithful less reliably than the strongest hosted models. Citation validation and abstention (PR-704) therefore matter more and should come early.
- Cost per token is derived from GPU cost and measured throughput, not from provider list prices. `model_prices` and `usage_events.cost_micros` (ADR 0006) hold these derived values.
- "Reserved provider capacity" for question embeddings (ADR 0006 §8) means reserved GPU capacity on the embedding server.
- The router's fallback and downgrade features (PR-504, PR-507) can only choose between self-hosted models.
- The hosted-LLM API key placeholder is removed from `.env.example`.
- Eval runs must be repeated after any model change, and the results recorded in the milestone file.

## Open questions (do not block acceptance)

- Which candidate models go into the size comparison (M4 and M6)?
- What is the GPU budget ceiling? It is answered by the size comparison. Until then, development uses Ollama on CPU or a single 24 GB GPU.
