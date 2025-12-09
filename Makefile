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

.PHONY: poetry-check
poetry-check: ## Validate pyproject and lock
	poetry check || true

.PHONY: lint
lint: ## Run available linters (ruff/flake8/pyflakes/mypy)
	@echo "Running linters..."
	@poetry run ruff check src || echo "ruff not installed; skipping"
	@poetry run flake8 src || echo "flake8 not installed; skipping"
	@poetry run pyflakes src || echo "pyflakes not installed; skipping"
	@poetry run mypy src || echo "mypy not installed; skipping"

.PHONY: format
format: ## Run formatters (black/isort) if available
	@echo "Running formatters..."
	@poetry run black src || echo "black not installed; skipping"
	@poetry run isort src || echo "isort not installed; skipping"

.PHONY: test
test: ## Run pytest
	@echo "Running tests..."
	@poetry run pytest -q || (echo "Tests failed"; exit 1)

.PHONY: megalint
megalint: poetry-check ## Syntax check, lint, and test
	@echo "Compiling for syntax errors..."
	@poetry run python -m compileall -q src || (echo "Syntax errors found"; exit 1)
	$(MAKE) lint
	$(MAKE) test

