import pytest

from barcode_api.core.config import get_config


@pytest.fixture
def app_config():
    return get_config()
