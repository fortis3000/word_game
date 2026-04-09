FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/ /app/src/
COPY configs/ /app/configs/
COPY scripts/ /app/scripts/

RUN uv venv && . .venv/bin/activate && uv sync --extra game

# Stamp cache-busting hashes into index.html
RUN .venv/bin/python scripts/stamp_cache.py

# Expose port
EXPOSE 8001