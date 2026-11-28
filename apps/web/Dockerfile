# Build context: repo root.  docker build -f apps/web/Dockerfile .
FROM node:24-alpine AS build
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm nx build web --configuration=production

FROM nginxinc/nginx-unprivileged:1.31-alpine AS runtime
# Pull in Alpine security fixes newer than the base image. CI rebuilds this stage without the
# layer cache (no-cache-filters: runtime), so every build gets the current fixes.
USER root
# hadolint ignore=DL3017
RUN apk upgrade --no-cache
USER 101
COPY --from=build /app/dist/apps/web/browser /usr/share/nginx/html
COPY apps/web/nginx/default.conf.template /etc/nginx/templates/default.conf.template
ENV BACKEND_URL=http://backend:3000
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
