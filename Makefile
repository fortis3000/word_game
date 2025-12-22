.PHONY: precommit

# Local precommit
precommit:
	bash ./precommit.sh

# Run tests
test:
	uv run python -m coverage run -m pytest -v tests/
	uv run python -m coverage report

# Clean cache and build artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cache and build artifacts cleaned"

# rm -rf build/ dist/ *.egg-info/
