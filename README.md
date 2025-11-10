# Word Game Project

[![CI](https://github.com/g-flas/word-game/actions/workflows/ci.yml/badge.svg)](https://github.com/g-flas/word-game/actions/workflows/ci.yml)

## Overview

This project is a word similarity game with a Telegram bot interface. It leverages a self-hosted sentence transformer model (embedding service) to calculate word embeddings and determine similarity between words. The project is structured as a modern Data Science application, featuring:

- **FastAPI-based embedding service** (`src/embedding_service`)
- **Core game logic** (`src/game`)
- **Telegram bot** (`src/telegram_bot`)
- **Shared utilities and clients** (`src/shared`, `src/utils`)
- **Testing suite** (`tests`)
- **Dockerized deployment** (`docker/`, `docker-compose.yaml`)

---

## Project Structure

```
├── data/                # Data folders (external, interim, processed, raw)
├── dicts/               # Dictionaries (e.g., German top1000)
├── docker/              # Dockerfiles and docker-compose.yaml
├── docs/                # Documentation and best practices
├── models/              # Model files (empty by default)
├── notebooks/           # Jupyter notebooks
├── references/          # Manuals and explanatory materials
├── reports/             # Generated analysis and figures
├── src/
│   ├── data/                # Data scripts
│   ├── embedding_service/   # FastAPI embedding service
│   ├── features/            # Feature engineering scripts
│   ├── game/                # Game logic
│   ├── models/              # (empty)
│   ├── shared/              # Shared code (e.g., embedding client)
│   ├── telegram_bot/        # Telegram bot code
│   ├── utils/               # Utilities (logger, etc.)
│   └── visualization/       # Visualization scripts
├── tests/               # Test suite (pytest)
├── .github/workflows/   # CI/CD configuration
├── Makefile             # Precommit and utility commands
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock              # Dependency lock file
├── README.md            # This file
```

---

## Setup & Usage

### 1. Python Environment

- **Python version:** 3.12+
- **Dependency management:** Uses `pyproject.toml` and [uv](https://github.com/astral-sh/uv) for fast installs and lockfile management.

**Create and activate a virtual environment:**
```bash
uv venv -p 3.12
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

**Sync dependencies:**
```bash
uv pip sync environment/dev-reqirements.txt
```

### 2. Linting & Formatting

- Uses [ruff](https://docs.astral.sh/ruff/) for both linting and formatting.

**Run checks:**
```bash
ruff format .
ruff check .
ruff check . --fix
```

### 3. Testing

- Uses `pytest`. Tests are in the `tests/` directory.

**Run tests:**
```bash
pytest
```

### 4. Docker

- Dockerfiles for embedding service and Telegram bot are in `docker/`.
- Use `docker-compose.yaml` to run services together.

**Start services:**
```bash
docker compose -f docker/docker-compose.yaml up --build
```

### 5. CI/CD

- GitHub Actions workflow in `.github/workflows/ci.yml` runs linting, tests, type checks, and builds Docker images.

### 6. Logging

- Use the logger utility in `src/utils/logger.py`. Supports plain text and JSON logging (set `LOG_FORMAT=json`).

**Example:**
```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("This is an info message.")
logger.error("This is an error message.")
```

To enable JSON logging:
```bash
export LOG_FORMAT=json
```

### 7. Game Data

- Example dictionary: `dicts/german/top1000.csv`

---

## Best Practices

- **File Paths:** Use absolute paths when interacting with files.
- **Code Style:** All Python code should be formatted with `ruff` according to the configuration in `pyproject.toml`.
- **Logging:** Use the logger utility from `src/utils/logger.py` for any new logging.
- **Testing:** Any new features should be accompanied by corresponding tests in the `tests` directory.

---

## Getting Started

1. **Clone the repository** (or create a new repo from this template).
2. **Install, compile, and activate the virtual environment** (see above).
3. **Adjust `pyproject.toml` and CI configuration** as needed.
4. **Add your source code to the `src` folder.**
5. **Enjoy coding!**

---

## Contributing

Feel free to open issues or submit pull requests for improvements, bug fixes, or new features.

---

## License

See [LICENSE](LICENSE) for details.
