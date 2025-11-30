.PHONY: precommit

# Local precommit
precommit:
	bash ./precommit.sh

# Run tests
test:
	uv run python -m pytest -v tests/
