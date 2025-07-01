FROM python:3.12.10-alpine AS builder

ARG PRIVATE_USERNAME
ARG PRIVATE_PASSWORD
ENV POETRY_HTTP_BASIC_TSD_USERNAME $PRIVATE_USERNAME
ENV POETRY_HTTP_BASIC_TSD_PASSWORD $PRIVATE_PASSWORD

ENV PYTHONUNBUFFERED 1
ENV DOCKER_CONTAINER 1
ENV POETRY_CACHE_DIR='/var/cache/pypoetry'
ENV POETRY_HOME='/usr/local'

WORKDIR /code/
COPY pyproject.toml poetry.lock README.md /code/

# Install dependencies
RUN apk add --no-cache \
    curl bash && \
    curl -sSL https://install.python-poetry.org | python3 - --version 2.1.2 && \
    poetry config virtualenvs.in-project true && \
    poetry config http-basic.tsd "$PRIVATE_USERNAME" "$PRIVATE_PASSWORD" && \
    poetry install --no-interaction --no-root --no-ansi --with ci

FROM python:3.12.10-alpine

WORKDIR /code/
COPY --from=builder /usr/bin/curl /usr/bin/curl
COPY --from=builder /bin/bash /bin/bash
COPY --from=builder /code /code

COPY src/ /code/
ENV PATH="/code/.venv/bin:$PATH"

EXPOSE 8000