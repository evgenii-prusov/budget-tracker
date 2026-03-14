import os
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import ArgumentError


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    try:
        make_url(database_url)
    except ArgumentError as exc:
        raise ValueError(f"Invalid DATABASE_URL: {database_url}") from exc
    return database_url


def get_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return [origin.strip() for origin in raw.split(",")]


def get_api_key() -> str:
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable is required")
    return api_key
