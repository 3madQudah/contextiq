# syntax=docker/dockerfile:1
#
# Two-stage build: a Node stage runs the Vite production build, then a
# lightweight nginx stage serves the resulting static files. Nothing from
# the Node stage (node_modules, the Vite dev server, source files) ships in
# the final image — only frontend/dist/.

############################
# Stage 1: build the static assets
############################
FROM node:20-slim AS builder

WORKDIR /app

# Separate COPY for the lockfile so this layer (the slow one) only
# re-invalidates when dependencies actually change, not on every source edit.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# src/services/api.js reads `import.meta.env.VITE_API_BASE_URL` -- Vite
# inlines that into the built JS bundle at `npm run build` time (a plain
# static build has no runtime env-var mechanism; there's nothing left to
# "read" once this step finishes). Sourced from a build ARG so
# docker-compose.yml can set it from .env; defaults to the same value
# frontend/.env.example uses for local (non-Docker) dev.
#
# IMPORTANT: this must be a URL reachable from the *browser*, not from
# inside the Docker network -- e.g. http://localhost:8000 (the backend's
# published host port), never an internal-network name like
# http://backend:8000. The compiled JS runs on the user's machine, not
# inside a container, so it can't resolve Docker's internal DNS.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

############################
# Stage 2: serve with nginx
############################
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -q -O /dev/null http://localhost/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
