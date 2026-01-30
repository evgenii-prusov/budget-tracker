import logging
import os
import sys


def _resolve_log_level() -> int:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = logging.getLevelName(level_name)
    if isinstance(level, int):
        return level
    raise ValueError(f"Invalid LOG_LEVEL: {level_name}")


def setup_logging() -> None:
    """Sets up the logging configuration for the application."""

    # Define the logging format
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )

    # Configure the root logger
    logging.basicConfig(
        level=_resolve_log_level(),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Logging infrastructure initialized")


def get_logger(name: str) -> logging.Logger:
    """Returns a logger with the specified name."""
    return logging.getLogger(name)
