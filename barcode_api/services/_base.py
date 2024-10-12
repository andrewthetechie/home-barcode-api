from logging import Logger

from barcode_api.core.config import Config


class BarcodeServiceBase:
    def __init__(self, config: Config, logger: Logger) -> None:
        self._config: Config = config
        self._logger: Logger = logger
