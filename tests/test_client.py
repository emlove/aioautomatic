"""Tests for automatic"""

import aiohttp

from aioautomatic.client import Client


def test_client():
    """Create a client object. Placeholder test."""
    client_id = 'mock_id'
    client_secret = 'mock_secret'
    aiohttp_session = aiohttp.ClientSession()
    Client(client_id, client_secret, aiohttp_session)
