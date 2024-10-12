import os
from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# ENV_PREFIX is the prefix used for all env vars for the api. defaults to BA for barcode_api
ENV_PREFIX = os.environ.get("barcode_api_env_prefix", "BA")


class LogLevel(StrEnum):
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"
    critical = "critical"


class Config(BaseSettings):
    env: str = "local"

    # logging options
    log_json: bool = False
    log_level: LogLevel = "info"

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)


@lru_cache
def get_config() -> Config:
    """Returns a cached Config object"""
    return Config()
