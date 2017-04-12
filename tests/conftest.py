"""Common fixtures for tests."""
from aioautomatic.client import Client

import pytest
from tests.common import SessionMock


@pytest.fixture
def aiohttp_session(event_loop):
    """Create a mock aiohttp session object."""
    session = SessionMock()
    session.loop = event_loop
    yield session


@pytest.fixture
def client(aiohttp_session):
    """Create an aioautomatic client connected to a mock aiohttp session."""
    client = Client('mock_id', 'mock_secret', aiohttp_session)
    yield client
