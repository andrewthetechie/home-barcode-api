from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from barcode_api.core.config import Config, get_config


class ConfigMiddleware(BaseHTTPMiddleware):
    """
    Adds an app config object to the request state

    """

    def __init__(self, app, config: Config | None = None):
        super().__init__(app)
        self.config = config if config is not None else get_config()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.config = self.config
        response: Response = await call_next(request)
        return response
