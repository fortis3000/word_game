FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY environment/telegram-bot-requirements.txt /tmp/requirements.txt

RUN uv venv
RUN uv pip install -r /tmp/requirements.txt

WORKDIR /app

COPY src/ /app/src/
COPY dicts/ /app/dicts/

# Run the bot
# CMD ["uv", "run", "python", "-m", "src.telegram_bot"]
