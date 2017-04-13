"""Common classes for tests."""
import asyncio

from unittest.mock import MagicMock


class AsyncMock(MagicMock):
    """MagicMock that returns coroutines instead of callables."""

    @asyncio.coroutine
    def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class SessionMock(AsyncMock):
    """Mock for aiohttp client session objects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__bool__ = lambda _: True
