FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY environment/embedding-model-requirements-cpu.txt /tmp/requirements.txt

RUN uv venv
RUN uv pip sync /tmp/requirements.txt

WORKDIR /app
COPY src/embedding_service /app/

# Set environment variable for model path
ENV MODEL_PATH=/app/model

# Expose the port
EXPOSE 8000

# Run the FastAPI application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]