# RAG and LLM standards

## Prompts

- Prompts are **versioned files** (`prompts/answer_v3.md` or similar) loaded and rendered by one module, not inline strings. A change to wording is a new version or a reviewed diff, with eval results. **[Review]**
- Template variables are explicit and escaped; retrieved text is inserted only inside delimited source blocks (see `security.md`).
- The prompt version id is recorded on every answer/trace.

## Models and config

- Model and embedding names, dimensions, temperature, max tokens, timeouts come from `Settings`, never literals in code. **[Review; hard-coded model strings flagged by reviewers]**
- Changing the embedding model or dimension means a new index version and a re-embed plan. Never mix vectors from different models in one collection or search.

```python
# bad
resp = await client.chat("gpt-4o", messages)
# good
resp = await self._llm.generate(request)  # LLMClient interface; model from settings.llm_model
```

## Interfaces and resilience

- Every model call (LLM, embedder, reranker) sits behind a small interface (`Protocol`: `LLMClient`, `Embedder`, `Reranker`) in core or the owning service. Providers are swappable, and tests inject fakes. **[Review]**
- Each adapter implements: explicit timeout, bounded retry with jittered backoff for 429/5xx/timeouts only, circuit breaker (open on repeated failures, fast-fail with a clear error), concurrency limit, token/cost accounting.
- Handle provider errors as domain exceptions (`LLMUnavailable`, `ContextTooLong`); never leak provider messages to clients.
- Degrade gracefully: if the reranker is down, fall back to vector order; if the LLM is down, return a clear 503, not a guess.

## Provenance

- Record `embedding_model`, `embedding_model_version`, `index_version`, `chunker_version` on every vector point and chunk row. **[Review]**
- Record `llm_model`, `model_version`, `prompt_version`, `retrieval params`, source chunk ids on every answer (trace and, when persisted, the answer row) so any answer can be reproduced and audited.

## Answers

- **Citations are mandatory**: every factual claim maps to one or more source chunks the user is permitted to see (document id, chunk id, page/offset). Validate that cited ids were in the retrieved set; drop or reject answers with invented citations. **[Review; a test must cover it]**
- **Abstain over guess**: if retrieval confidence is low, no source supports the answer, or the context is empty after ACL filtering, answer "I could not find this in the documents you have access to" with no speculation. Abstention is measured in eval.
- Never answer from model memory about tenant facts; instructions say "use only the sources".
- Citations and snippets are ACL-filtered before the model sees them.

## Evaluation evidence

- Any change to retrieval, chunking, embeddings, reranking, query rewriting, prompts or model choice **must include eval results in the PR**: Recall@k, MRR (retrieval) and faithfulness / citation accuracy / abstention (answers), before vs after, on the same golden set version. **[Review; CI `eval` validates the dataset]**
- No regression larger than the agreed threshold on any headline metric (start: **-1 point absolute** on Recall@k and MRR, **-2** on faithfulness; recorded in `eval/README` once set). Intentional trade-offs need justification and an owner sign-off.
- Golden set changes (`eval/datasets/`) are reviewed by CODEOWNERS; never edit expected answers to make a change pass without saying so. Dataset must validate: `docqa-eval validate`. **[Enforced: CI `eval` job]**
- Add a golden item for every real failure found.

## Testing

- Deterministic unit tests mock LLMs, embedders and rerankers with fakes returning fixed outputs. No real provider calls in CI unit tests. **[Review]**
- Test the pipeline around the model: prompt rendering, citation validation, abstention path, ACL filter construction, retry and breaker behaviour.
- Live-model evals are a separate, opt-in job with a budget; results are stored with the model and prompt versions.
