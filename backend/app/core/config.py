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
