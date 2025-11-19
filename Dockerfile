ARG PYTHON_VERSION=3.9
ARG NODE_VERSION=20

FROM python:${PYTHON_VERSION}-slim AS base

FROM base AS builder-base

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_NO_INTERACTION=1 \
  PATH="$PATH:/app/.venv/bin" \
  PYTHONPATH="$PYTHONPATH:/app/.venv/lib/python${PYTHON_VERSION}/site-packages/" \
  POETRY_VERSION=2.2.1

# System deps:
RUN apt-get update && apt-get install -y build-essential unzip wget python3-dev
RUN pip install "poetry==$POETRY_VERSION" && \
  poetry config virtualenvs.in-project true && \
  poetry config virtualenvs.path .venv

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock alembic.ini /app/
RUN poetry install --without dev --no-root

FROM builder-base as backend-builder

COPY src /app/src
RUN poetry install --without dev

FROM builder-base as worker-builder
RUN apt-get install -y libpq-dev
RUN poetry install --without dev --no-root -E worker

COPY migrations /app/migrations
COPY src /app/src
RUN poetry install --without dev -E worker

FROM builder-base as tester
RUN apt-get install -y libpq-dev redis-server
RUN poetry install --without dev --no-root -E worker -E test

COPY migrations /app/migrations
COPY src /app/src
RUN poetry install --without dev -E worker -E test
ENV PYTHONTRACEMALLOC=40
ENV PYTHONASYNCIODEBUG=1
ENTRYPOINT ["poetry", "run", "pytest", "--cov"]
CMD []

FROM node:${NODE_VERSION}-alpine as frontend-base

FROM frontend-base as frontend-prep-stage
WORKDIR /app
COPY web/unchanging-ink/package.json ./
RUN sed -i -e 's/  "version": ".*",/  "version": "0.0.0",/' package.json

FROM frontend-base as frontend-build-stage
WORKDIR /app

COPY web/unchanging-ink/package-lock.json ./
COPY --from=frontend-prep-stage /app/package.json ./
RUN npm ci
COPY web/unchanging-ink .

RUN npm run build

FROM frontend-base as frontend-install-stage
WORKDIR /app
COPY web/unchanging-ink/package-lock.json ./
COPY --from=frontend-prep-stage /app/package.json ./
RUN npm ci --omit=dev

FROM frontend-base as frontend
WORKDIR /app

COPY --from=frontend-install-stage /app/node_modules/ /app/node_modules/
COPY --from=frontend-build-stage /app/package.json /app/
COPY --from=frontend-build-stage /app/.output/ /app/.output/
CMD ["node", ".output/server/index.mjs"]

FROM base as worker
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV PYTHONPATH=/app/.venv/lib/python${PYTHON_VERSION}/site-packages/ PATH="$PATH:/app/.venv/bin"
CMD "/app/.venv/bin/unchanging-ink_worker"
COPY --from=worker-builder /app/ /app/

FROM base AS backend
WORKDIR /app
ENV PYTHONPATH=/app/.venv/lib/python${PYTHON_VERSION}/site-packages/ PATH="$PATH:/app/.venv/bin"
CMD ["sanic", "unchanging_ink.server:app", "--host=0.0.0.0", "--port=8000", "--fast"]
COPY --from=backend-builder /app/ /app/
