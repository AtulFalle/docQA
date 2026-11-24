# docqa-eval

Evaluation tooling for docQA: a golden-set schema, binary-relevance retrieval metrics, and a
validator CLI. It depends only on pydantic and runs standalone.

```bash
PYTHONPATH=eval/src python3 -m docqa_eval.cli validate eval/datasets/golden_v0.jsonl --corpus eval/corpus/sample
PYTHONPATH=eval/src python3 -m docqa_eval.cli stats eval/datasets/golden_v0.jsonl
```

## Golden set format

`datasets/*.jsonl` holds one JSON object per line. Blank lines are ignored, and parse errors report
the file and line number.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | str | Unique within the file. |
| `tenant_id` | str | Must match the tenant of every cited document. |
| `asking_user` | str | The user the question is asked as. Group membership decides ACL. |
| `question` | str | The user's question, verbatim. |
| `question_type` | enum | See below. |
| `expected_behavior` | `answer` / `abstain` / `deny` | What a correct system does. |
| `gold` | list of `{doc_id, page?, chunk_id?, quote?}` | Evidence a correct answer is grounded in. |
| `reference_answer` | str or null | Required when the behaviour is `answer`. |
| `tags` | list of str | Free-form. Used for `acl:<doc_id>` markers and `injection`. |
| `notes` | str or null | Human context, such as the prior turn for conversational items. |

Rules enforced by the schema:

- `answer` requires non-empty `gold` and a `reference_answer`.
- `unanswerable` requires `expected_behavior` = `abstain` and empty `gold`.
- `acl_trap` requires `expected_behavior` = `abstain` or `deny`.

`validate` also checks duplicate ids, that every cited `doc_id` is in `manifest.json`, that each
cited document belongs to the item's tenant, and that each manifest entry has a matching `<doc_id>.md`.

## Question types

- `factual`: one document, one fact.
- `multi_hop`: the answer needs facts from two or more pages or documents.
- `aggregation`: the answer is a set, count, filter or ranking over several documents.
- `unanswerable`: the corpus does not contain the answer. The system must abstain.
- `acl_trap`: the answer exists, but the asking user's groups cannot read the source. The
  system must deny or abstain. Tag each restricted document as `acl:<doc_id>`. The seed test
  checks that the user really lacks access.
- `conversational`: a follow-up that depends on earlier turns. Put the prior turn in `notes`.

Tag `injection` marks items whose corpus contains adversarial text, such as a hidden instruction
in an HTML comment. Expected behaviour is still the honest answer.

## Corpus and manifest

Each document is `<corpus>/<doc_id>.md`, with `<!-- page: N -->` markers that start a new page.
`manifest.json` maps `doc_id` to `{tenant_id, acl_groups, title}`. A user can read a document if
any of their groups appears in `acl_groups`.

`eval/corpus/sample/` is a fictional seed corpus: three résumés (group `hr`), two contracts
(group `legal`) and one leave policy (group `all`). The seed users are defined in
`SEED_USER_GROUPS` in `src/docqa_eval/dataset.py`:

- `u_hr_1`: `hr`, `all`
- `u_legal_1`: `legal`, `all`
- `u_eng_1`: `all`

The seed set exists to smoke-test the pipeline. It is not a quality benchmark.

## Growing the set to 100-200 items over the real corpus

1. Copy the real documents into a new corpus directory such as `eval/corpus/<name>/`. Write
   `manifest.json` with each document's tenant and ACL groups. Keep the layout and page markers.
2. Define each real user and their groups in a table next to `SEED_USER_GROUPS`, or load it from
   a file. The ACL tests depend on it.
3. Draft questions per document cluster, covering all six question types. Aim for roughly
   30 to 40 per type and at least 15 `acl_trap` and 15 `unanswerable` items. Include
   conversational items that carry `notes` with the earlier turn.
4. For each `answer` item, locate the gold pages by hand, and write `reference_answer` from the
   text. Put a short `quote` in the evidence where the phrasing is ambiguous. Do not generate gold
   with the system under test.
5. Have a second person review each item. Record disagreements in `notes`.
6. Run `validate` after each batch. Keep `golden_v0.jsonl` as the smoke set and write the real
   set as a new file, such as `golden_v1.jsonl`.

## Metrics

`metrics.py` provides `recall_at_k`, `precision_at_k`, `hit_rate_at_k`, `reciprocal_rank`, `mrr`,
and `ndcg_at_k`. All use binary relevance. An empty relevant set scores 0.0. `precision_at_k`
divides by `k` even when fewer than `k` results come back.

## Tests

```bash
PYTHONPATH=eval/src python3 -m pytest eval/tests -q -p no:cacheprovider
```
