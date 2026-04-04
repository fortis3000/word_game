# AGENT GUIDE - Word Game Project

## 1. Project Overview
This project is a word similarity game with a Telegram bot and a Web UI interface. It uses a self-hosted sentence transformer model (embedding service) to calculate word embeddings and determine similarity.

**Components:**
- **FastAPI-based embedding service**: `src/embedding_service`
- **Game Application (Web UI & FastAPI)**: `src/game`
- **Telegram bot**: `src/telegram_bot`
- **Prometheus Monitoring**: Metrics collection via `/metrics` endpoints.
- **Shared utilities**: `src/shared`, `src/utils`

## 2. Technical Standards & Tech Stack
- **Language**: Python 3.12+
- **Dependency Management**: [uv](https://github.com/astral-sh/uv)
- **Linting/Formatting**: [ruff](https://docs.astral.sh/ruff/)
- **Testing**: `pytest`
- **Monitoring**: Prometheus
- **Deployment**: Docker & Docker Compose

## 3. Project Structure
```text
├── configs/             # Configuration files (e.g., prometheus.yml)
├── data/                # Data folders (external, interim, processed, raw)
├── dicts/               # Dictionaries (e.g., German top1000)
├── docker/              # Dockerfiles and docker-compose.yaml
├── docs/                # Documentation
├── models/              # Model files
├── notebooks/           # Jupyter notebooks
├── src/
│   ├── data/                # Data scripts
│   ├── embedding_service/   # FastAPI embedding service
│   ├── features/            # Feature engineering scripts
│   ├── game/                # Game logic, FastAPI web app, and static UI
│   ├── shared/              # Shared code (e.g., embedding client)
│   ├── telegram_bot/        # Telegram bot code
│   ├── utils/               # Utilities (logger, etc.)
│   └── visualization/       # Visualization scripts
├── tests/               # Test suite (pytest)
├── Makefile             # Utility commands
├── pyproject.toml       # Configuration
└── README.md            # Main documentation
```

## 4. Development Workflow

### Dependency Management
- **Install/Sync**: `uv sync --all-extras`
- **Add Dependency**: `uv add <package>`
- **Run Scripts**: `uv run python -m ...`

### Code Quality (MANDATORY)
Run the following before submitting any changes:
```bash
make precommit
```
*This runs `ruff format` and `ruff check --fix`.*

### Testing
- Run all tests: `make test` (or `uv run python -m pytest`)
- **Requirement**: Any new feature must have corresponding tests in `tests/`.

### Running Locally
Use Docker Compose to spin up the services:
```bash
docker compose -f docker/docker-compose.yaml up --build
```
*Web apps should default to port 10000+ if running outside docker.*

## 5. Coding Standards & Best Practices

### Logging (CRITICAL)
**ALWAYS** use the project's custom logger. Do not use standard `logging` or `print`.
```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Message")
```

### Imports
**Internal project imports:**
- **Functions**: Use namespace imports (`from module import module_name` → `module_name.function()`)
- **Classes/Exceptions**: Use direct imports (`from module import TheClass`)

### Python Best Practices
- **Paths**: Use `pathlib.Path` instead of `os.path`.
- **Typing**: Use modern syntax (e.g., `list[int]`, `str | None` for optional).
- **Control Flow**: Use guarding clauses (early returns) to avoid nested code.
- **Async**: Use `async`/`await` for I/O bound operations.
- **Files**: Always use absolute paths when interacting with files.

### Configuration
- Check `configs/` or environment variables.
- Do not hardcode secrets or absolute local paths that won't work in Docker.