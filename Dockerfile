ARG PYTHON_VERSION=3.9
ARG NODE_VERSION=14

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
  POETRY_VERSION=1.1.13

# System deps:
RUN apt-get update && apt-get install -y build-essential unzip wget python-dev
RUN pip install "poetry==$POETRY_VERSION" && \
    poetry config virtualenvs.in-project true && \
    poetry config virtualenvs.path .venv

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock alembic.ini /app/
RUN poetry install --no-dev --no-root

FROM builder-base as backend-builder

COPY src /app/src
RUN poetry install --no-dev

FROM builder-base as worker-builder
RUN apt-get install -y libpq-dev
RUN poetry install --no-dev --no-root -E worker

COPY migrations /app/migrations
COPY src /app/src
RUN poetry install --no-dev -E worker

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
COPY doc ./content/doc

RUN npm run build

FROM frontend-base as frontend
WORKDIR /app
COPY web/unchanging-ink/package-lock.json ./
COPY --from=frontend-prep-stage /app/package.json ./
RUN npm ci --production

COPY --from=frontend-build-stage /app/package.json /app/nuxt.config.js /app/
COPY --from=frontend-build-stage /app/.nuxt/ /app/.nuxt/
COPY --from=frontend-build-stage /app/content/ /app/content/
CMD ["npm", "run", "start"]

FROM base as worker
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV PYTHONPATH=/app/.venv/lib/python${PYTHON_VERSION}/site-packages/ PATH="$PATH:/app/.venv/bin"
CMD "/app/.venv/bin/unchanging-ink_worker"
COPY --from=worker-builder /app/ /app/

FROM base AS backend
WORKDIR /app
ENV PYTHONPATH=/app/.venv/lib/python${PYTHON_VERSION}/site-packages/ PATH="$PATH:/app/.venv/bin"
CMD "/app/.venv/bin/unchanging-ink"
COPY --from=backend-builder /app/ /app/
