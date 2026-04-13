# --- Stage 1: Install dependencies with uv ---
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build
COPY pyproject.toml ./

RUN uv pip install --system --no-cache \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.34" \
    "sqlmodel>=0.0.22" \
    "psycopg[binary]>=3.2" \
    "alembic>=1.14" \
    "ldap3>=2.9" \
    "apscheduler>=3.10,<4" \
    "pydantic-settings>=2.7"

# --- Stage 2: Slim runtime image ---
FROM python:3.12-slim

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
