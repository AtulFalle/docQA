# 0002. Deployment target

- Status: Proposed. Decision needed before M2 (first deployed environment). Recommendation updated 2026-11-28.

## Context

The API, ingestion worker and migration job are container images (see `.github/workflows/cd.yml`, which builds and pushes them to GHCR). The stack needs Postgres, Qdrant, Redis, Temporal and object storage in production. Some of these are available as managed services, and others are not. The choice affects operating cost, team skills, and how much infrastructure we own.

## Options

1. **Managed container platform** (for example ECS Fargate, Cloud Run or Azure Container Apps). Stateless API and workers run as services. Databases, Redis and object storage are managed. Qdrant and Temporal may run as managed or self-hosted services.
   - Pros: low operational load, simple scaling, fits the stateless service split.
   - Cons: fewer knobs for GPU or large-memory workloads; Qdrant and Temporal hosting options vary by cloud.
2. **Kubernetes** (managed control plane such as EKS, GKE or AKS, with Helm or Kustomize).
   - Pros: one model for every component, mature options for stateful services, room for GPU node pools if self-hosted models are adopted (see ADR 0003).
   - Cons: highest operational cost; needs a platform owner.
3. **Single VM with Docker Compose** (the local compose file, hardened).
   - Pros: cheapest and fastest to start; no new platform to learn.
   - Cons: no high availability, manual upgrades, and backups are our responsibility. Acceptable only for a pilot with a small corpus.

## Recommended default

*Updated 2026-11-28.* ADR 0003 now requires self-hosted models, and the original condition for revisiting Kubernetes ("if self-hosted models … are needed") has been met. The recommendation is therefore **option 2, Kubernetes, kept portable**:

- Use only self-hostable components: Postgres, Qdrant, Redis, Temporal, RustFS, Langfuse, and vLLM for models. Use no cloud-only managed services, so the same charts can run in our own cloud account, on our own servers, or inside a customer's infrastructure.
- GPU node pools for generation, embedding and reranking, sized from the model-size comparison in M4 and M6 (ADR 0003).
- kind for the full local stack, with Argo CD GitOps as proposed in Discussion #135.
- Managed Postgres or object storage is still allowed when the chosen target offers it, as long as it stays S3- and Postgres-compatible.

Where it runs (which cloud, on-prem, or customer infrastructure) is still undecided. Option 3 stays acceptable for a pilot with a small corpus, provided it has a GPU.

## Open questions

- Which cloud provider does the organisation already use, and does it have a standard container platform?
- Is there an operations or platform team to own the cluster, or does the product team run the services?
- Is Temporal Cloud acceptable, or must Temporal be self-hosted? (Temporal Cloud stores workflow payloads. Ours carry object keys only, per ADR 0006, but this must be checked against ADR 0004.)
- Where will it run: our own cloud account, our own servers, or customer infrastructure?
- What GPU capacity can the target provide (see the tiers in ADR 0003)?
- What availability target applies (for example, a stated uptime for query latency)?
- Is a pilot on a single VM acceptable before the production environment exists?

## Consequences

Once decided, add the `deploy` job to `.github/workflows/cd.yml` with a bound GitHub environment (for example `staging` then `prod`), and record the decision as a new ADR that supersedes this one or marks it Accepted.
