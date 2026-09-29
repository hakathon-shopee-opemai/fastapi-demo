# ---- Build stage: resolve deps with uv into a venv ----
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS build
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
# Cache dependency layer separately from source.
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project
COPY . .
RUN uv sync --no-dev

# ---- Runtime stage ----
FROM python:3.13-alpine AS runtime
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8000
# Entrypoint is the FastAPI app factory at app/main.py (to be implemented).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
