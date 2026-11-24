# Architecture Decision Records

Decisions that shape the system are recorded here as short numbered documents. Each ADR describes the context, the decision (or the options, when it is still open), and the consequences.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-monorepo-and-stack.md) | Monorepo layout and core stack | Accepted (superseded in part by 0005) |
| [0002](0002-deployment-target.md) | Deployment target | Proposed (decide before M2) |
| [0003](0003-llm-and-embedding-provider.md) | LLM and embedding provider | Proposed (decide before M1 and M2) |
| [0004](0004-data-residency.md) | Data residency | Proposed (decide before M2) |
| [0005](0005-angular-nestjs-python-ai-services.md) | Angular UI, NestJS backend, Python internal AI services | Accepted |

## Process

1. Copy [`template.md`](template.md) to `NNNN-short-title.md`, using the next free number.
2. Set **Status** to `Proposed`. Open a PR with the ADR alone so the options can be reviewed.
3. When the decision is made, change the status to `Accepted` and update the index. Do not rewrite an accepted ADR. To change a decision, write a new ADR that marks the old one `Superseded by NNNN`.
4. Tick the matching item in the milestone file (for example `docs/milestones/M0.md`).

Status values: `Proposed`, `Accepted`, `Superseded by NNNN`, `Rejected`.
