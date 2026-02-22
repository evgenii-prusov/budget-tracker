import time
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "")
        query_string = scope.get("query_string", b"").decode()
        url = f"{path}?{query_string}" if query_string else path
        status_code = {"value": 500}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code["value"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            process_time = time.perf_counter() - start_time
            logger.info("%s %s - %s - %.4fs", method, url, status_code["value"], process_time)
