FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.2 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml ./
COPY .build_env ./.env_buildtime

RUN set -a && . ./.build_env && set +a && export PATH="${UV_PROJECT_ENVIRONMENT}/bin:${PATH}" && uv sync --no-dev && rm ./.build_env

ENV PATH="/app/.venv/bin:${PATH}"

COPY src ./src
COPY certs ./certs

CMD ["sh", "-c", "uv run uvicorn --app-dir src app:app --host \"${HOST:-0.0.0.0}\" --port \"${PORT:-8000}\""]
