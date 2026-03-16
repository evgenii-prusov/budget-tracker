FROM python:3.12-slim

# Copy uv binary from the official uv image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create a non-root user to run the application
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Install dependencies first — this layer is cached until lock file changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Add the virtual-env binaries to PATH so alembic/uvicorn can be called directly
# Disable .pyc generation (ephemeral container, no benefit) and unbuffer stdout for logs
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy application code and Alembic configuration
COPY alembic/ alembic/
COPY alembic.ini alembic.ini
COPY app/ app/

# Hand ownership to the app user and switch to it
RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/openapi.json')" || exit 1

# Run database migrations then start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
