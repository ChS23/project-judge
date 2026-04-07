FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base

WORKDIR /app

COPY pyproject.toml uv.lock ./

FROM base AS prod
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ src/
RUN uv sync --frozen --no-dev
CMD ["uv", "run", "python", "-m", "judge"]

FROM base AS eval
RUN uv sync --frozen --no-install-project
COPY src/ src/
COPY tests/ tests/
RUN uv sync --frozen
CMD ["uv", "run", "python", "-m", "pytest", "tests/test_eval/", "-v", "--tb=short", "-s"]
