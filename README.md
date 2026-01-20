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

**Install dependencies:**
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates .venv automatically)
uv sync
```

**Activate virtual environment (optional if using `uv run`):**
```bash
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 2. Linting & Formatting

- Uses [ruff](https://docs.astral.sh/ruff/) for both linting and formatting.
- A `Makefile` is provided for convenience.

**Run checks (via Makefile):**
```bash
make precommit
```

**Run checks (manually):**
```bash
uv run ruff format .
uv run ruff check . --fix
```

### 3. Testing

- Uses `pytest`. Tests are in the `tests/` directory.

**Run tests:**
```bash
make test
# OR
uv run python -m pytest
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

- **Dependency Management:** Use `uv` for all dependency operations (`uv add`, `uv remove`, `uv sync`).
- **Code Quality:** Run `make precommit` before pushing changes to ensure code is formatted and linted with `ruff`.
- **File Paths:** Use absolute paths when interacting with files.
- **Logging:** Use the logger utility from `src/utils/logger.py` for any new logging.
- **Testing:** Any new features should be accompanied by corresponding tests in the `tests` directory. Run `make test` to verify.

---

## PvP Features & Language Support

### 1. Challenge via Inline Query
Users can type `@<BotName>` in any chat to view **3 Challenge Options** (English, German, Russian).
- **Deep Linking**: Generates a link like `https://t.me/<BotName>?start=<seed>_<lang>`.
- **Auto-Start**: The recipient clicks "Accept" and the game opens **immediately** in the chosen language.

### 2. Deterministic Gameplay
- Games started via challenge are **seeded**. 
- Both players receive the **exact same order of words** and refills for fair comparison.

### 3. Score Sharing
- Upon finishing, users can click "Share Score 🏆".
- This opens the Telegram chat picker to post a score card: *"I scored X! Can you beat me?"*.
- The card includes a "Challenge" button for friends to replay the **same seed**.

---

## Getting Started

1. **Clone the repository** (or create a new repo from this template).
2. **Install dependencies:** Run `uv sync`.
3. **Adjust `pyproject.toml` and CI configuration** as needed.
4. **Add your source code to the `src` folder.**
5. **Enjoy coding!**

---

## Contributing

Feel free to open issues or submit pull requests for improvements, bug fixes, or new features.

---

## License

See [LICENSE](LICENSE) for details.
