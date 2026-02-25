.PHONY: install test lint fmt type-check clean

install:
	uv sync --all-extras

test:
	uv run pytest

test-cov:
	uv run pytest --cov=kalshi_intel --cov-report=term-missing

lint:
	uv run ruff check src/ tests/

fmt:
	uv run ruff format src/ tests/

type-check:
	uv run mypy src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache .ruff_cache dist build *.egg-info
