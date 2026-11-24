# 0002. Deployment target

- Status: Proposed. Decision needed before M2 (first deployed environment).

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

Option 1 (managed container platform) for the first deployed environment, with managed Postgres, Redis and object storage. Revisit Kubernetes if self-hosted models or large Qdrant clusters are needed. Keep the images cloud-neutral so the choice stays reversible.

## Open questions

- Which cloud provider does the organisation already use, and does it have a standard container platform?
- Is there an operations or platform team to own the cluster, or does the product team run the services?
- Is Temporal Cloud acceptable, or must Temporal be self-hosted?
- What availability target applies (for example, a stated uptime for query latency)?
- Is a pilot on a single VM acceptable before the production environment exists?

## Consequences

Once decided, add the `deploy` job to `.github/workflows/cd.yml` with a bound GitHub environment (for example `staging` then `prod`), and record the decision as a new ADR that supersedes this one or marks it Accepted.
