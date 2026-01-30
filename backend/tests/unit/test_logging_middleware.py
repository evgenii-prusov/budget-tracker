import asyncio
import logging

from app.api.middleware import LoggingMiddleware
from app.core.logging_config import get_logger


async def _app(scope, receive, send):
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [],
        }
    )
    await send({"type": "http.response.body", "body": b""})


def test_logging_middleware_includes_query_params(caplog):
    middleware = LoggingMiddleware(_app)
    logger = get_logger("app.api.middleware")

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/accounts",
        "query_string": b"skip=1&limit=2",
    }

    caplog.set_level(logging.INFO, logger=logger.name)

    async def receive():
        return {"type": "http.request"}

    async def send(message):
        return None

    asyncio.run(middleware(scope, receive, send))

    assert "GET /accounts?skip=1&limit=2 - 200" in caplog.text
