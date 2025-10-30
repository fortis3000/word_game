FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies including curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY environment/embedding-model-requirements-cpu.txt /tmp/requirements.txt

RUN uv venv
RUN uv pip install -r /tmp/requirements.txt

WORKDIR /app
COPY src/embedding_service /app/

# Set environment variable for model path
ENV MODEL_PATH=/app/model

# Expose the port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the FastAPI application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]