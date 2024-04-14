.PHONY: setup
setup: ## Install Poetry dependencies
	@echo "🚀 Installing Poetry deps"
	@poetry install --with dev
	@poetry run pre-commit install

.PHONY: poetry-lock
poetry-lock: ## Lock Poetry dependencies
	@echo "🚀 Locking Poetry deps"
	@poetry lock

.PHONY: shell
shell: ## Run Django shell_plus
	@echo "🚀 Running Django app locally"
	@poetry run python src/manage.py shell_plus

.PHONY: build
build: ## Run local tests using Docker
	@echo "🚀 Building Docker container..."
	@docker-compose -f docker/docker-compose.yml build

.PHONY: test
test: build ## Run local tests using Docker
	@echo "🚀 Running local tests"
	@docker-compose -f docker/docker-compose.test.yml run test

.PHONY: local-test
local-test: ## Run Django tests locally
	@echo "🚀 Running Django tests locally"
	@
	@poetry run python src/manage.py test src/

.PHONY: local-run
local-run: ## Run Django app locally
	@echo "🚀 Running Django app locally"
	@cd src/ && poetry run python manage.py runserver

.PHONY: docker-run
docker-run: build ## Run local instance using Docker
	@echo "🚀 Running local instance"
	@docker-compose -f docker/docker-compose.stack.yml up -d

.PHONY: help
help: ## Display available make commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help