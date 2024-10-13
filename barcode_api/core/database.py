import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, ClassVar

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from barcode_api.core.config import Config, get_config

ERROR_MESSAGES: dict[str, str] = {"NOT_INITIALIZED": "DatabaseSessionManager is not initialized"}


class Base(DeclarativeBase):
    # https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession
    __mapper_args__: ClassVar[dict[str, Any]] = {"eager_defaults": True}


# Heavily inspired by https://praciano.com.br/fastapi-and-async-sqlalchemy-20-with-pytest-done-right.html
class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] | None = None):
        if engine_kwargs is None:
            engine_kwargs = dict()
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine, expire_on_commit=False)

    async def close(self):
        if self._engine is None:
            raise Exception(ERROR_MESSAGES["NOT_INITIALIZED"])
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception(ERROR_MESSAGES["NOT_INITIALIZED"])

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception(ERROR_MESSAGES["NOT_INITIALIZED"])

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


config: Config = get_config()
sessionmanager = DatabaseSessionManager(config.sqlalchemy_url, {"echo": config.echo_sql})


async def get_db_session():
    async with sessionmanager.session() as session:
        yield session


@asynccontextmanager
async def database_lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()
