# Running LL via Docker

## Prerequisites

**Enable Docker BuildKit** (required for secure credential handling):
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

**Set private repository credentials**:
```bash
export POETRY_HTTP_BASIC_TSD_USERNAME="your_username"
export POETRY_HTTP_BASIC_TSD_PASSWORD="your_password"
```

## Run Test
1) Run `docker compose -f docker-compose.test.yml build`
2) Run `docker compose -f docker-compose.test.yml run --rm test`

## Run LL Locally

1) Copy `.env.example` to `.env` and fill it in with required secrets in `spacelaunchnow/settings`
2) Run `docker compose up`
3) Open a browser to `http://localhost:8080/`

### Restore Database
**Example**
`docker exec -i sln_db pg_restore -U spacelaunchnow_prod_user -v -d sln_db < spacelaunchnow.backup &> restore.log`

## Run full stack locally
Run `docker compose -f docker-compose.stack.yml up -d --build`
Then either attach to the running LL image or connect via browser.

## Security Notes

- Credentials are securely mounted as BuildKit secrets at `/run/secrets/private_username` and `/run/secrets/private_password`
- Environment variables are not persisted in the final Docker image
- Requires Docker Compose 3.8+ and BuildKit enabled