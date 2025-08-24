.PHONY: setup lint test run build audit
setup:
	uv sync --all-extras --dev
	pre-commit install

lint:
	uv run ruff check .
	uv run ruff format .
	uv run mypy .

test:
	uv run pytest --cov=.

run:
	uv run python -m app.cli run --seconds 22

audit:
	uv run pip-audit || true
	uv run bandit -r app || true
