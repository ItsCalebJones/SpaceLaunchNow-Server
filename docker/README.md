# Running LL via Docker

## Run Test
1) Run `docker-compose -f docker-compose.test.yml build`
2) Run `docker-compose -f docker-compose.test.yml run --rm test`

## Run LL Locally

1) Copy `.env.example` to `.env` and fill it in with required secrets in `spacelaunchnow/settings`
2) Run `docker-compose up`
3) Open a browser to `http://localhost:8080/`

### Restore Database
**Example**
`docker exec -i sln_db pg_restore -U spacelaunchnow_prod_user -v -d spacelaunchnow_local < spacelaunchnow_2024.01.11-16.42.44.backup &> restore.log`

## Run full stack locally
Run `docker-compose -f docker-compose.stack.yml up -d --build`
Then either attach to the running LL image or connect via browser.