"""Test fixtures."""

from collections.abc import Generator

import pytest

from tests.test_util.aiohttp import AiohttpClientMocker, mock_aiohttp_client


@pytest.fixture
def aioclient_mock() -> Generator[AiohttpClientMocker, None, None]:
    """Fixture to mock aioclient calls."""
    with mock_aiohttp_client() as mock_session:
        yield mock_session
