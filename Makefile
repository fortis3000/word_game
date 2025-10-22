.PHONY: precommit requirements_lint

POETRY_PATH = poetry
PYTHON_FILES = **/*.py *.py

# Install linting requirements
requirements_lint:
	${POETRY_PATH} install --only codestyle

# Local precommit
precommit: requirements_lint
	bash ./precommit.sh