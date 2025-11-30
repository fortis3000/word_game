#!/usr/bin/env bash
echo "Running pre-commit hook"

echo "Formatting with ruff"
uv run ruff format .

echo "Linting with ruff"
uv run ruff check . --fix

echo "Finished"
