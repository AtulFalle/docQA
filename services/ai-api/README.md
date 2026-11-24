# docqa-ai-api

Internal AI service (FastAPI): retrieval and answer generation. It is called only by the NestJS backend (`apps/backend`) over internal HTTP and is never exposed to browsers; auth, tenancy and ACLs are enforced by the backend.

Run locally: `uvicorn docqa_ai_api.main:app --reload --port 8001` (compose publishes it on 8001).

Endpoints: `/healthz`, `/readyz`, `/v1/info`.
