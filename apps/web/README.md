# web

Angular 22 (standalone, zoneless, signals) single-page app for docQA. The browser only calls relative `/api/v1/*`.

## Develop
`pnpm nx serve web` starts the dev server (and the backend via `dependsOn`). `proxy.conf.json` forwards `/api` to http://localhost:3000.

## Test
- Unit (Vitest): `pnpm nx test web`
- Types: `pnpm nx typecheck web`
- Lint: `pnpm nx lint web`
- E2E (Playwright, API mocked, no backend needed): `pnpm nx e2e web-e2e` (serves the production build via `web:serve-static`)

## Build
`pnpm nx build web --configuration=production` -> `dist/apps/web/browser`

## Docker
Build from the repo root: `docker build -f apps/web/Dockerfile -t docqa-web .`
Run: `docker run -p 8080:8080 -e BACKEND_URL=http://backend:3000 docqa-web`
nginx serves the SPA, proxies `/api/` to `BACKEND_URL`, and exposes `/healthz`.
