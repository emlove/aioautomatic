"""Common fixtures for tests."""
from aioautomatic.client import Client
from aioautomatic.session import Session

import pytest
from tests.common import AsyncMock, SessionMock


@pytest.fixture
def aiohttp_session(event_loop):
    """Create a mock aiohttp session object."""
    session = SessionMock()
    session.loop = event_loop
    yield session


@pytest.fixture
def client(aiohttp_session):
    """Create an aioautomatic client connected to a mock aiohttp session."""
    client = Client("mock_id", "mock_secret", aiohttp_session)
    yield client


@pytest.fixture
def session(aiohttp_session):
    """Create a test aioautomatic session."""
    client = AsyncMock()
    client.client_session = aiohttp_session
    client.request_kwargs = {}
    data = {
        "access_token": "123",
        "refresh_token": "ABCD",
        "expires_in": 12345,
        "scope": ("scope:location scope:vehicle:profile "
                  "scope:user:profile scope:trip"),
    }
    session = Session(client, **data)
    yield session
