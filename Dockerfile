FROM python:3.8-slim AS base

FROM base AS builder

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_NO_INTERACTION=1 \
  PATH="$PATH:/app/.venv/bin" \
  PYTHONPATH="$PYTHONPATH:/app/.venv/lib/python3.8/site-packages/" \
  POETRY_VERSION=1.1.5

# System deps:
RUN apt-get update && apt-get install -y build-essential unzip wget python-dev libpq-dev
RUN pip install "poetry==$POETRY_VERSION" && \
    poetry config virtualenvs.in-project true && \
    poetry config virtualenvs.path .venv

WORKDIR /app

# Generate requirements and install *all* dependencies.
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-dev --no-root

COPY . /app
RUN poetry install --no-dev

FROM base as helper
RUN apt-get update && apt-get install -y libpq5
COPY --from=builder /app/ app/
WORKDIR /app
ENV PYTHONPATH=/app/.venv/lib/python3.8/site-packages/ PATH="$PATH:/app/.venv/bin"
CMD "/bin/true"

FROM base AS runtime
COPY --from=builder /app/ app/
WORKDIR /app
ENV PYTHONPATH=/app/.venv/lib/python3.8/site-packages/ PATH="$PATH:/app/.venv/bin"
CMD "/app/.venv/bin/unchanging-ink"
