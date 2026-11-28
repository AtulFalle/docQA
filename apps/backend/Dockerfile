# Build context: repository root.  docker build -f apps/backend/Dockerfile .
FROM node:26-alpine AS deps
WORKDIR /repo
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM deps AS build
COPY . .
# prisma-generate runs through dependsOn; prune emits package.json + pruned lockfile into dist.
RUN pnpm nx run backend:prune --configuration=production

# One-shot migration runner (used by compose).
FROM deps AS migrate
COPY apps/backend/prisma apps/backend/prisma
COPY apps/backend/prisma.config.ts apps/backend/prisma.config.ts
CMD ["pnpm","prisma","migrate","deploy","--config","apps/backend/prisma.config.ts"]

# Must stay last: the default target of a plain `docker build`.
FROM node:26-alpine AS runtime
ENV NODE_ENV=production
WORKDIR /app
RUN corepack enable
COPY --from=build --chown=node:node /repo/dist/apps/backend/ ./
# npm is unused at runtime and its bundled deps carry CVEs; drop it after the install.
# --ignore-scripts: the Prisma client is generated and bundled at build time, so no
# install script (prisma, @prisma/engines, protobufjs, scarf) is needed here.
RUN pnpm install --prod --frozen-lockfile --ignore-scripts && chown -R node:node /app \
  && rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/api/v1/health || exit 1
CMD ["node","main.js"]
