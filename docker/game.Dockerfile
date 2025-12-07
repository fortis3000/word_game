FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/ /app/src/
COPY configs/ /app/configs/

RUN uv venv && . .venv/bin/activate && uv sync --extra game

# Expose port
EXPOSE 8001