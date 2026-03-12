FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.2 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml ./

RUN uv sync --no-dev

COPY src ./src

CMD ["uv", "run", "streamlit", "run", "src/app.py"]
