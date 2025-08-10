# syntax=docker/dockerfile:1
FROM python:3.12.10-alpine AS builder

ENV PYTHONUNBUFFERED=1
ENV DOCKER_CONTAINER=1
ENV POETRY_CACHE_DIR='/var/cache/pypoetry'
ENV POETRY_HOME='/usr/local'
ENV PATH="/usr/local/bin:$PATH"

WORKDIR /code/
COPY pyproject.toml poetry.lock README.md /code/

# Install dependencies using BuildKit secrets (most secure approach)
RUN --mount=type=secret,id=private_username \
    --mount=type=secret,id=private_password \
    apk add --no-cache curl bash && \
    curl -sSL https://install.python-poetry.org | python3 - --version 2.1.2 && \
    poetry config virtualenvs.in-project true && \
    poetry config http-basic.tsd "$(cat /run/secrets/private_username)" "$(cat /run/secrets/private_password)" && \
    poetry install --no-interaction --no-root --no-ansi --with ci && \
    # Clear poetry credentials and secrets from memory
    poetry config --unset http-basic.tsd

FROM python:3.12.10-alpine

WORKDIR /code/
COPY --from=builder /usr/bin/curl /usr/bin/curl
COPY --from=builder /bin/bash /bin/bash
COPY --from=builder /code /code

COPY src/ /code/
ENV PATH="/code/.venv/bin:$PATH"

EXPOSE 8000