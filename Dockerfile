FROM python:3.12.10-alpine AS builder

ARG PRIVATE_USERNAME
ARG PRIVATE_PASSWORD
ENV POETRY_HTTP_BASIC_TSD_USERNAME=$PRIVATE_USERNAME
ENV POETRY_HTTP_BASIC_TSD_PASSWORD=$PRIVATE_PASSWORD

ENV PYTHONUNBUFFERED=1
ENV DOCKER_CONTAINER=1
ENV POETRY_CACHE_DIR='/var/cache/pypoetry'
ENV POETRY_HOME='/usr/local'
ENV PATH="/usr/local/bin:$PATH"

WORKDIR /code/
COPY pyproject.toml poetry.lock README.md /code/

# Install dependencies with connection testing
RUN apk add --no-cache curl bash && \
    curl -sSL https://install.python-poetry.org | python3 - --version 2.1.2 && \
    export PATH="/usr/local/bin:$PATH" && \
    echo "=== Poetry Installation Check ===" && \
    poetry --version && \
    echo "=== Configuring Poetry ===" && \
    poetry config virtualenvs.in-project true && \
    echo "=== Testing TSD Repository Connectivity ===" && \
    if curl -f -s https://pypi.thespacedevs.com/simple/ > /dev/null; then \
        echo "✅ TSD repository is reachable"; \
    else \
        echo "❌ Cannot reach TSD repository"; \
        exit 1; \
    fi && \
    echo "=== Checking Credentials ===" && \
    if [ -z "$PRIVATE_USERNAME" ] || [ -z "$PRIVATE_PASSWORD" ]; then \
        echo "❌ ERROR: TSD credentials not provided"; \
        echo "USERNAME: '${PRIVATE_USERNAME}'"; \
        echo "PASSWORD length: ${#PRIVATE_PASSWORD}"; \
        exit 1; \
    else \
        echo "✅ Credentials provided (user: $PRIVATE_USERNAME)"; \
    fi && \
    echo "=== Testing Authenticated Access ===" && \
    if curl -u "$PRIVATE_USERNAME:$PRIVATE_PASSWORD" -f -s https://pypi.thespacedevs.com/simple/django-launch-library/ > /dev/null; then \
        echo "✅ Authenticated access successful"; \
    else \
        echo "❌ Authenticated access failed"; \
        echo "This usually means invalid credentials or package doesn't exist"; \
        exit 1; \
    fi && \
    echo "=== Configuring Poetry Authentication ===" && \
    poetry config http-basic.tsd "$PRIVATE_USERNAME" "$PRIVATE_PASSWORD" && \
    echo "✅ Poetry authentication configured" && \
    echo "=== Installing Dependencies ===" && \
    poetry install --no-interaction --no-root --no-ansi --with ci || \
    (echo "❌ DEPENDENCY INSTALLATION FAILED" && \
     echo "This is usually caused by:" && \
     echo "1. Invalid TSD repository credentials" && \
     echo "2. django-launch-library package not available in TSD repository" && \
     echo "3. Version 21.34.2 not published to TSD repository" && \
     echo "4. Network connectivity issues" && \
     echo "" && \
     echo "To debug:" && \
     echo "1. Verify credentials work: curl -u USERNAME:PASSWORD https://pypi.thespacedevs.com/simple/django-launch-library/" && \
     echo "2. Check if package exists in TSD repository" && \
     echo "3. Verify version 21.34.2 is published" && \
     echo "4. Consider updating poetry.lock: poetry lock --no-update" && \
     exit 1)

FROM python:3.12.10-alpine

WORKDIR /code/
COPY --from=builder /usr/bin/curl /usr/bin/curl
COPY --from=builder /bin/bash /bin/bash
COPY --from=builder /code /code

COPY src/ /code/
ENV PATH="/code/.venv/bin:$PATH"

EXPOSE 8000