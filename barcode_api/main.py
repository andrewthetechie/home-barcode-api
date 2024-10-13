from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

from barcode_api.controller import CONTROLLERS
from barcode_api.core.config import get_config
from barcode_api.core.database import database_lifespan
from barcode_api.core.middlewares.config_middleware import ConfigMiddleware
from barcode_api.core.middlewares.logging_middleware import CustomLoggingMiddleware

config = get_config()
app = FastAPI(lifespan=database_lifespan, title=config.api_name, docs_url=config.docs_url)

app.add_middleware(ConfigMiddleware, config=config)
app.add_middleware(CustomLoggingMiddleware, enable_json_logs=config.log_json, log_level=config.log_level.value.upper())
app.add_middleware(CorrelationIdMiddleware)

for controller in CONTROLLERS:
    app.include_router(controller)
