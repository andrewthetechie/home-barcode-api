import os
from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# ENV_PREFIX is the prefix used for all env vars for the api. defaults to BA for barcode_api
ENV_PREFIX = os.environ.get("barcode_api_env_prefix", "ba_")


class LogLevel(StrEnum):
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"
    critical = "critical"


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)

    env: str = "local"

    # logging options
    log_json: bool = False
    log_level: LogLevel = "info"

    # db config
    sqlalchemy_driver: str = "sqlite+aiosqlite"
    sqlite_path: str = "/ba.db"
    postgres_host: str | None = None
    postgres_port: str | None = None
    postgres_user: str | None = None
    postgres_pass: str | None = None
    postgres_db: str | None = None

    # spotify config
    spotify_client_id: str
    spotify_client_secret: str

    # discogs config
    discogs_token: str

    @property
    def sqlalchemy_url(self) -> str:
        if "sqlite" in self.sqlalchemy_driver:
            url = f"{self.sqlalchemy_driver}://{self.sqlite_path}"
        if "postgres" in self.sqlalchemy_driver:
            url = f"{self.sqlalchemy_driver}://{self.postgres_user}:{self.postgres_pass}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        return url


@lru_cache
def get_config() -> Config:
    """Returns a cached Config object"""
    return Config()
