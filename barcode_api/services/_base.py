from logging import Logger
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from barcode_api.core.config import Config
from barcode_api.core.database import Base

ModelType = TypeVar("ModelType", bound="Base")


class BarcodeServiceBase:
    MODEL: type[ModelType]

    def __init__(self, config: Config, logger: Logger, db_session: AsyncSession) -> None:
        self._config: Config = config
        self._logger: Logger = logger
        self._db_session = db_session

    async def _get_fom_cache(self, value: str, key: str = "barcode") -> ModelType | None:
        async with self._db_session.begin():
            result = await self._db_session.scalar(select(self.MODEL).where(getattr(self.MODEL, key) == value))
        return result

    async def _add_to_cache(self, instance: ModelType) -> None:
        async with self._db_session.begin():
            self._db_session.add(instance)
            await self._db_session.commit()
