import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        # Log request
        method = request.method
        url = request.url.path

        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        status_code = response.status_code

        logger.info("%s %s - %s - %.4fs", method, url, status_code, process_time)

        return response
