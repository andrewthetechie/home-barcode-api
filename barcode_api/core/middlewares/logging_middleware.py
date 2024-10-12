# This code is modified from https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e

import time
from collections.abc import Callable

import structlog
from asgi_correlation_id import correlation_id
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from uvicorn.protocols.utils import get_path_with_query_string

from barcode_api.core.logging import configure_logger


class CustomLoggingMiddleware(BaseHTTPMiddleware):
    """
    Adds an access log using the struclog formatted loggers

    Adds the app logger to each request's state so controllers can access it
    """

    def __init__(self, app, enable_json_logs: bool = False, log_level: str = "INFO"):
        super().__init__(app)
        configure_logger(enable_json_logs=enable_json_logs, log_level=log_level)
        self.access_logger = structlog.stdlib.get_logger("api.access")
        self.api_error_logger = structlog.stdlib.get_logger("api.error")
        self.app_logger = structlog.stdlib.get_logger("app")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.logger = self.app_logger
        request.state.error_logger = self.api_error_logger
        structlog.contextvars.clear_contextvars()
        # These context vars will be added to all log entries emitted during the request
        request_id = correlation_id.get()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.perf_counter_ns()

        response: Response = await call_next(request)
        process_time = time.perf_counter_ns() - start_time
        status_code = response.status_code
        url = get_path_with_query_string(request.scope)
        client_host = request.client.host
        http_method = request.method
        http_version = request.scope["http_version"]
        # Recreate the Uvicorn access log format, but add all parameters as structured information
        self.access_logger.info(
            f"""{client_host} - "{http_method} {url} HTTP/{http_version}" {status_code}""",
            http={
                "url": str(request.url),
                "status_code": status_code,
                "method": http_method,
                "request_id": request_id,
                "version": http_version,
            },
            network={"ip": client_host},
            duration=process_time,
        )
        response.headers["X-Process-Time"] = str(process_time / 10**9)
        return response
