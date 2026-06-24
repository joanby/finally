# syntax=docker/dockerfile:1

# ---- Stage 1: build the Next.js static export ----
FROM node:20-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python backend + bundled static frontend ----
FROM python:3.12-slim AS backend
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# El backend resuelve la raíz del proyecto 3 niveles por encima de app/db/,
# por eso colocamos el código en /app/backend para que la BD caiga en /app/db.
WORKDIR /app/backend

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY backend/ ./
RUN uv sync --frozen --no-dev

# Estáticos del frontend servidos por FastAPI desde app/static/
COPY --from=frontend /frontend/out ./app/static

# La BD vive en el volumen montado en /app/db
ENV FINALLY_DB_PATH=/app/db/finally.db
ENV PATH="/app/backend/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
