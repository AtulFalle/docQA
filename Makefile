.DEFAULT_GOAL := help
.PHONY: help dev backend db-migrate db-migrate-dev js-check e2e format check lint-imports deps-check audit setup up down logs ps up-app ai-api worker lint fmt typecheck test test-unit eval-validate docker-build contracts contracts-check verify-observability clean

COMPOSE = docker compose -f infra/docker/docker-compose.yml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

setup: ## Install workspace deps and git hooks
	corepack enable
	pnpm install
	uv sync --all-packages --group dev
	uv run pre-commit install --install-hooks
	git config commit.template .gitmessage

up: ## Start core infra (Postgres, Redis, RustFS, Qdrant, Temporal, Langfuse, LGTM)
	$(COMPOSE) up -d

down: ## Stop infra containers (keeps volumes)
	$(COMPOSE) down

logs: ## Follow infra container logs
	$(COMPOSE) logs -f

ps: ## Show infra container status
	$(COMPOSE) ps

up-app: ## Start infra + all app containers (web :8088, backend :3000, ai-api :8001, worker)
	$(COMPOSE) --profile app up -d --build

verify-observability: ## Check one request is traceable in Loki + Tempo (needs `make up-app`)
	uv run python -I infra/scripts/verify_observability.py

ai-api: ## Run the internal AI service locally with reload on :8001
	uv run uvicorn docqa_ai_api.main:app --reload --host 0.0.0.0 --port 8001

dev: ## Run Angular (:4200) + NestJS (:3000) with the /api dev proxy
	pnpm nx serve web

backend: ## Run the NestJS backend only (:3000)
	pnpm nx serve backend

db-migrate: ## Apply Prisma migrations (apps/backend/prisma)
	pnpm db:migrate

db-migrate-dev: ## Create a new Prisma migration from schema changes
	pnpm db:migrate:dev

js-check: ## TS gates: prettier, lint, typecheck, unit tests, builds
	pnpm format:check
	pnpm nx run-many -t lint lint-styles typecheck test
	pnpm nx run-many -t build

e2e: ## Playwright e2e for the web app
	pnpm nx e2e web-e2e

format: ## Format TS/HTML/SCSS/JSON with Prettier
	pnpm format

worker: ## Run the Temporal ingestion worker locally
	uv run docqa-worker

lint: ## Ruff lint and format check
	uv run ruff check .
	uv run ruff format --check .
	uv run python tools/check_file_length.py

fmt: ## Auto-fix lint and format
	uv run ruff check --fix .
	uv run ruff format .

lint-imports: ## Enforce architecture boundaries (import-linter)
	uv run lint-imports

deps-check: ## Declared vs imported dependencies per package (deptry)
	cd libs/py-core && uv run deptry src
	cd services/ai-api && uv run deptry src
	cd services/ingestion-worker && uv run deptry src
	cd eval && uv run deptry src

audit: ## Known-vulnerability scan of resolved dependencies (pip-audit)
	uv export --all-packages --no-emit-workspace --no-hashes --format requirements-txt -o requirements-audit.txt
	uvx pip-audit@2.7.3 -r requirements-audit.txt --no-deps --disable-pip

check: lint lint-imports deps-check typecheck test-unit eval-validate js-check ## All fast quality gates (run before pushing)

typecheck: ## Mypy over the source packages
	uv run mypy libs/py-core/src services/ai-api/src services/ingestion-worker/src eval/src

test: ## Run all tests (includes integration; needs infra up)
	uv run pytest

test-unit: ## Run unit tests only (no infra needed)
	uv run pytest -m "not integration"

eval-validate: ## Validate golden eval dataset against sample corpus
	uv run docqa-eval validate eval/datasets/golden_v0.jsonl --corpus eval/corpus/sample

contracts: ## Regenerate OpenAPI documents, ai-api client types and event models
	bash tools/contracts/generate.sh

CONTRACT_OUTPUTS = libs/shared/contracts/openapi libs/shared/contracts/src/generated libs/py-core/src/docqa_core/events

contracts-check: contracts ## Fail if the committed contract artefacts are stale
	@git diff --exit-code -- $(CONTRACT_OUTPUTS) || (echo 'Contracts are stale: run `make contracts` and commit the result.' && exit 1)
	@test -z "$$(git status --porcelain --untracked-files=all -- $(CONTRACT_OUTPUTS))" || (git status --short -- $(CONTRACT_OUTPUTS) && echo 'Untracked generated files: run `make contracts` and commit them.' && exit 1)

docker-build: ## Build all app images (web, backend, ai-api, worker)
	$(COMPOSE) --profile app build backend-migrate backend web ai-api worker

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml htmlcov dist build
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
