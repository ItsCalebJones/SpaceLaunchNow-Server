FROM python:3.10.4-slim-buster AS builder

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

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
     git \
     gcc \
     curl \
     python-dev \
     libsqlite3-dev \
     libpng-dev \
     libjpeg-dev
RUN rm -rf /var/lib/apt/lists/*

# Installing `poetry` package manager:
# https://github.com/python-poetry/poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.8.2
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-interaction --no-root --no-ansi --with ci

FROM python:3.10.4-slim-buster

WORKDIR /code/
COPY --from=builder /code /code

COPY src/ /code/
ENV PATH="/code/.venv/bin:$PATH"

EXPOSE 8000