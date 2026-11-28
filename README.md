# docQA

Production retrieval-augmented question answering over large document volumes. Users ask questions and get answers that cite the source passages, and every answer respects per-document access control.

The project is in milestone M0 (foundations): repository, local infrastructure, data model, evaluation seed, observability and CI/CD. Answer generation arrives in M1.

## Architecture

The browser talks only to the Angular UI and the NestJS backend. The backend is the public API and the system of record; the Python AI services are internal and never exposed to browsers. Decision record: [ADR 0005](docs/adr/0005-angular-nestjs-python-ai-services.md).

| Part | Stack | Role |
|------|-------|------|
| `apps/web` | Angular 22 | Browser UI |
| `apps/backend` | NestJS 12, Prisma 7 | Public API (`/api/v1`), auth, tenancy, ACLs, Postgres schema and migrations |
| `services/ai-api` | FastAPI (internal, :8001) | Retrieval and answers |
| `services/ingestion-worker` | Temporal workers (Python) | Ingest: validate, extract, chunk, embed, index |
| `eval/` | Python | Golden dataset, metrics, CLI |
| `libs/shared/contracts` | TypeScript (`@docqa/contracts`) | Request and response types shared by web and backend |
| `libs/py-core` | Python (`docqa-core`) | Settings (env + YAML), provider registry, domain types and errors, logging, telemetry, SQLAlchemy mirror of the schema |

### Request path

```
Browser
  -> Angular UI            dev: Angular proxy /api     prod: nginx /api
  -> NestJS backend        /api/v1 (auth, tenant, ACL)
  -> internal HTTP         only the backend calls ...
  -> Python ai-api         retrieval and answers (FastAPI)

Temporal -> ingestion-worker   validate -> extract -> chunk -> embed -> index
```

Stores: Postgres (tenants, documents, ACLs, chunks, jobs, audit log, with RLS), Qdrant (vectors filtered by tenant and ACL), Redis (cache, rate limits), RustFS / S3 (raw uploads). Traces and metrics go to OpenTelemetry and Grafana; LLM traces go to Langfuse.

Full design: `architecture/production-rag-plan-v1.md`. Decisions: `docs/adr/`. Milestone status: `docs/milestones/`. Engineering rules: `docs/engineering/`.

## Repository layout

```
docqa/
├── apps/web/                   Angular UI
├── apps/web-e2e/               Playwright end-to-end tests (API mocked)
├── apps/backend/               NestJS backend, Prisma schema and migrations (apps/backend/prisma)
├── apps/backend-e2e/           end-to-end tests against a running backend
├── libs/shared/contracts/      @docqa/contracts: shared TypeScript types
├── libs/py-core/               docqa-core: settings, registry, domain types, logging, telemetry, DB models
├── services/ai-api/            docqa-ai-api: internal FastAPI AI service
├── services/ingestion-worker/  docqa-workers: Temporal workflows and activities
├── eval/                       docqa-eval: golden dataset, metrics, CLI, sample corpus
├── infra/                      docker/docker-compose.yml and Postgres init scripts
├── tools/                      repo scripts
├── docs/                       ADRs, engineering standards, milestones
├── architecture/               architecture plan
├── .github/                    CI, CD, security, CodeQL, PR template
├── package.json, nx.json       pnpm workspace and Nx targets (TypeScript)
├── pyproject.toml              uv workspace root and shared Python tooling
├── Makefile                    Python shortcuts (make help)
└── .env.example                all settings with local defaults
```

## Prerequisites

- **Node 24** with corepack. Corepack provides the pinned pnpm version (`packageManager` in `package.json`).
- **Docker Desktop** (Windows: with the WSL 2 backend), running.
- **uv** (Python package and project manager). Windows, PowerShell:
  `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Python 3.12**. uv installs it if needed: `uv python install 3.12`.
- **make** (optional, Python shortcuts only). On Windows, use the PowerShell commands below instead.

## Quickstart: Windows PowerShell

Run these from the repository root.

```powershell
# 1. Enable pnpm and install TypeScript dependencies
corepack enable
pnpm install

# 2. Install Python workspace dependencies and git hooks
uv sync --all-packages --group dev
uv run pre-commit install

# 3. Create local settings
Copy-Item .env.example .env

# 4. Start infrastructure (first start pulls images and creates volumes)
docker compose -f infra/docker/docker-compose.yml up -d

# 5. Apply database migrations (Prisma, owned by apps/backend)
pnpm db:migrate

# 6. Start the web app; this also starts the backend
pnpm nx serve web
```

Open http://localhost:4200. In a second terminal, start the internal AI service and, optionally, the worker:

```powershell
uv run uvicorn docqa_ai_api.main:app --reload --host 0.0.0.0 --port 8001
uv run docqa-worker
```

To run the AI service and worker as containers instead of on the host:

```powershell
docker compose -f infra/docker/docker-compose.yml --profile app up -d --build
```

To stop: `docker compose -f infra/docker/docker-compose.yml down`. To wipe all data (volumes, including the init scripts' databases), add `-v`.

## Quickstart: make (Python only)

Requires `make` (for example via Git Bash, WSL or Chocolatey on Windows). These targets cover the Python stack; use the pnpm commands above for the web and backend.

```bash
make setup      # uv sync + pre-commit install
make up         # start infrastructure
make ai-api     # internal AI service with reload on :8001
make worker     # ingestion worker
make help       # list every target
```

## Local service ports

| Service | URL / address | Notes |
|---------|---------------|-------|
| Web (dev) | http://localhost:4200 | `pnpm nx serve web`; proxies `/api` to the backend |
| Web (container) | http://localhost:8088 | nginx image (`--profile app`), proxies `/api` to the backend |
| Backend | http://localhost:3000 | Public API under `/api/v1`; health at `/healthz` and `/readyz` |
| ai-api | http://localhost:8001 | Internal; OpenAPI docs at `/docs` (not reachable from browsers in production) |
| Temporal UI | http://localhost:8080 | Workflow history |
| Temporal gRPC | localhost:7233 | Used by the worker |
| RustFS console | http://localhost:9001/rustfs/console/ | Login `rustfsadmin` / `rustfsadmin` (local only) |
| RustFS API | http://localhost:9000 | S3-compatible endpoint |
| Qdrant | http://localhost:6333 | Dashboard at `/dashboard` |
| Grafana | http://localhost:3002 | Traces, logs and metrics from `otel-lgtm`; moved from 3000 so it does not clash with the backend |
| Langfuse | http://localhost:3001 | LLM traces (used from M1) |
| Postgres | localhost:5432 | User and database `docqa` / `docqa` (local only) |
| Redis | localhost:6379 | |

## Running tests

TypeScript (Nx, pnpm):

```powershell
pnpm nx affected -t lint typecheck test build   # lint, types, unit tests, builds for changed projects
pnpm format:check                                # Prettier
pnpm nx e2e web-e2e                              # Playwright, API mocked
pnpm nx e2e backend-e2e                          # needs the backend and infrastructure running
```

Python (uv):

```powershell
uv run pytest -m "not integration"   # unit tests, no infrastructure needed
uv run pytest                        # everything; needs the infrastructure running
uv run ruff check .
uv run ruff format --check .
uv run mypy libs/py-core/src services/ai-api/src services/ingestion-worker/src eval/src
```

Integration tests need `DOCQA_TEST_DATABASE_URL` (see `.env.example`). The database must already be migrated by Prisma (`pnpm db:migrate`); the Python mirror is checked by `test_core_schema_contract.py`. Schema drift is checked with `pnpm db:drift`.

## Evaluation

The golden dataset lives in `eval/datasets/golden_v0.jsonl` and is checked against the sample corpus in `eval/corpus/sample/`:

```powershell
uv run docqa-eval validate eval/datasets/golden_v0.jsonl --corpus eval/corpus/sample
uv run docqa-eval stats eval/datasets/golden_v0.jsonl
```

The `eval` package has no dependencies beyond pydantic, so this runs on a fresh checkout. Retrieval and answer metrics are added in M1.

## CI/CD

- **CI** (`.github/workflows/ci.yml`) runs on every pull request and on pushes to `main`: Ruff lint and format, mypy, Python tests with coverage against a Postgres service, eval dataset validation, Docker image builds, and compose file validation. The TypeScript jobs (`CI / js`, `CI / e2e-web`, and Prisma migrate and drift in `CI / test`) are the target state and land with the apps. Details: [docs/engineering/ci-cd.md](docs/engineering/ci-cd.md).
- **CD** (`.github/workflows/cd.yml`) runs on pushes to `main` and `v*` tags: builds the `ai-api` and `ingestion-worker` images and pushes them to GitHub Container Registry (`ghcr.io/<owner>/docqa-ai-api`, `docqa-workers`). The `deploy` step is a placeholder until ADR 0002 is accepted.
- **Dependabot** checks GitHub Actions, Python dependencies and Docker base images weekly.

## Code quality

Ruff, strict mypy, import-linter boundaries, a coverage ratchet and security scanning gate every Python change; Prettier, ESLint (including Nx module boundaries), strict TypeScript and the web and backend tests gate TypeScript changes once their CI jobs land. The rules, the gate table and the Definition of Done are in [docs/engineering/](docs/engineering/README.md). The enforced settings live in `eslint.config.mjs`, `tsconfig.base.json`, `.prettierrc` and `pyproject.toml`.

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md): branching, commit style, local setup, PR checklist
- [docs/engineering/](docs/engineering/README.md): engineering standards for TypeScript, Angular, NestJS and Python
- [docs/adr/](docs/adr/): architecture decision records, including open decisions (deployment, LLM provider, data residency)
- [docs/milestones/M0.md](docs/milestones/M0.md): M0 checklist mapped to files
- [architecture/production-rag-plan-v1.md](architecture/production-rag-plan-v1.md): architecture plan
