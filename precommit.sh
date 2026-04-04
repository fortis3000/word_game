#!/usr/bin/env bash
set -e
echo "Running pre-commit hook"

echo "Formatting with ruff"
uv run ruff format .

echo "Linting with ruff"
uv run ruff check . --fix

echo "Linting markdown"
uv run pymarkdown scan .

echo "Finished"
