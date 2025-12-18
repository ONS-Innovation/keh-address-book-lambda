.PHONY: all
all: ## Show the available make targets.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

.PHONY: clean
clean: ## Clean the temporary files.
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf megalinter-reports
	rm -rf site

.PHONY: poetry-check
poetry-check: ## Validate pyproject and lock
	poetry check || true

.PHONY: format
format: ## Run formatters
	poetry run black src
	poetry run ruff check src --fix

.PHONY: lint
lint:
	poetry run black --check src
	poetry run ruff check src
	make mypy

.PHONY: test
test: ## Run pytest
	poetry run pytest -n auto --cov=src --cov-report term-missing --cov-fail-under=90

.PHONY: mypy
mypy:  ## Run mypy.
	poetry run mypy --config-file mypy.ini src

.PHONY: install
install:  ## Install the dependencies excluding dev and docs.
	poetry install --only main --no-interaction

.PHONY: install-dev
install-dev:  ## Install the dependencies including dev.
	poetry install --with dev --no-interaction

.PHONY: install-docs
install-docs:  ## Install the dependencies including docs.
	poetry install --with docs --no-interaction


.PHONY: megalint
megalint:  ## Run the mega-linter.
	docker run --platform linux/amd64 --rm \
		-v /var/run/docker.sock:/var/run/docker.sock:rw \
		-v $(shell pwd):/tmp/lint:rw \
		oxsecurity/megalinter:v8

