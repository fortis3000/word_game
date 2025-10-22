#!/usr/bin/env bash
echo "List of changes fields comparing to master branch"
#git diff --stat master
export CHANGED_FILES=$(git diff --name-only --diff-filter=d master -- '***.py')

if [ -z "$CHANGED_FILES" ]; then
  echo "No Python files were changed, skipping linting"
  exit 0;
fi

echo
ruff format $CHANGED_FILES --config pyproject.toml
ruff check $CHANGED_FILES --fix --config pyproject.toml

echo
echo "Finished"