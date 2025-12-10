# syntax=docker/dockerfile:1
FROM python:3.12.19-alpine AS builder

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
    # Configure private repository access - REQUIRED for django-launch-library
    echo "🔍 Checking for BuildKit secrets..." && \
    USERNAME_SECRET=$(cat /run/secrets/private_username 2>/dev/null || echo "") && \
    PASSWORD_SECRET=$(cat /run/secrets/private_password 2>/dev/null || echo "") && \
    if [ -n "$USERNAME_SECRET" ] && [ -n "$PASSWORD_SECRET" ]; then \
        echo "✅ Configuring private repository access..."; \
    else \
        echo "❌ ERROR: Private repository credentials are required for django-launch-library dependency"; \
        echo "   Please ensure PRIVATE_USERNAME and PRIVATE_PASSWORD secrets are provided"; \
        echo "   Secret files checked: /run/secrets/private_username, /run/secrets/private_password"; \
        ls -la /run/secrets/ || echo "   /run/secrets/ directory not found"; \
        exit 1; \
    fi && \
    echo "📦 Installing dependencies..." && \
    apk add --no-cache curl bash && \
    curl -sSL https://install.python-poetry.org | python3 - --version 2.1.2 && \
    poetry config virtualenvs.in-project true && \
    poetry config http-basic.tsd "$USERNAME_SECRET" "$PASSWORD_SECRET" && \
    poetry install --no-interaction --no-root --no-ansi --with ci && \
    # Clear poetry credentials and secrets from memory
    poetry config --unset http-basic.tsd

FROM python:3.12.19-alpine

WORKDIR /code/
COPY --from=builder /usr/bin/curl /usr/bin/curl
COPY --from=builder /bin/bash /bin/bash
COPY --from=builder /code /code

COPY src/ /code/
ENV PATH="/code/.venv/bin:$PATH"

EXPOSE 8000