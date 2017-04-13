"""Tests for automatic base objects."""
import asyncio
import aiohttp
from aioautomatic import base
from aioautomatic import exceptions

import pytest
from unittest.mock import patch
from tests.common import AsyncMock


@patch.object(base, 'aiohttp')
def test_create_root_api_object(mock_aiohttp, aiohttp_session):
    """Test the first api object creation."""
    mock_aiohttp.ClientSession.return_value = aiohttp_session
    mock_kwargs = {
        'arg1': 10,
        'arg2': 20,
    }
    obj = base.BaseApiObject(None, request_kwargs=mock_kwargs)
    assert obj.client_session == aiohttp_session
    assert obj.loop == aiohttp_session.loop
    assert obj.request_kwargs == mock_kwargs


def test_pass_aiohttp_session(aiohttp_session):
    """Test the first api object creation."""
    obj = base.BaseApiObject(None, client_session=aiohttp_session)
    assert obj.client_session == aiohttp_session
    assert obj.loop == aiohttp_session.loop


def test_parent_inheritance(aiohttp_session):
    """Test the first api object creation."""
    mock_kwargs = {
        'arg1': 10,
        'arg2': 20,
    }
    child_kwargs = {
        'arg3': 30,
    }
    parent = base.BaseApiObject(None, request_kwargs=mock_kwargs,
                                client_session=aiohttp_session)
    child = base.BaseApiObject(parent, request_kwargs=child_kwargs)
    assert child.client_session == aiohttp_session
    assert child.loop == aiohttp_session.loop
    assert child.request_kwargs == {
        'arg1': 10,
        'arg2': 20,
        'arg3': 30,
    }


def test_api_get(aiohttp_session):
    """Test the get api object method."""
    mock_kwargs = {
        "timeout": 10,
    }
    obj = base.BaseApiObject(None, request_kwargs=mock_kwargs,
                             client_session=aiohttp_session)

    resp = AsyncMock()
    resp.status = 200
    mock_json = {
        "mock_attr", "mock_val",
    }
    resp.json.return_value = mock_json
    aiohttp_session.request.return_value = resp

    mock_request = {
        "request_attr": "request_data",
    }
    result = aiohttp_session.loop.run_until_complete(obj._get(
        "mock_url", mock_request))

    assert result == mock_json
    assert aiohttp_session.request.called
    assert len(aiohttp_session.request.mock_calls) == 2
    assert aiohttp_session.request.mock_calls[0][1][0] == "GET"
    assert aiohttp_session.request.mock_calls[0][1][1] == "mock_url"
    assert aiohttp_session.request.mock_calls[0][2]["data"] == mock_request
    assert aiohttp_session.request.mock_calls[0][2]["timeout"] == 10


def test_api_post(aiohttp_session):
    """Test the post api object method."""
    mock_kwargs = {
        "timeout": 10,
    }
    obj = base.BaseApiObject(None, request_kwargs=mock_kwargs,
                             client_session=aiohttp_session)

    resp = AsyncMock()
    resp.status = 200
    mock_json = {
        "mock_attr", "mock_val",
    }
    resp.json.return_value = mock_json
    aiohttp_session.request.return_value = resp

    mock_request = {
        "request_attr": "request_data",
    }
    result = aiohttp_session.loop.run_until_complete(obj._post(
        "mock_url", mock_request))

    assert result == mock_json
    assert aiohttp_session.request.called
    assert len(aiohttp_session.request.mock_calls) == 2
    assert aiohttp_session.request.mock_calls[0][1][0] == "POST"
    assert aiohttp_session.request.mock_calls[0][1][1] == "mock_url"
    assert aiohttp_session.request.mock_calls[0][2]["data"] == mock_request
    assert aiohttp_session.request.mock_calls[0][2]["timeout"] == 10


def test_request_timeout(aiohttp_session):
    """Test the api request timeout."""
    obj = base.BaseApiObject(None, client_session=aiohttp_session)

    @asyncio.coroutine
    def side_effect(*args, **kwargs):
        raise asyncio.TimeoutError()

    aiohttp_session.request.side_effect = side_effect

    with pytest.raises(exceptions.TransportError):
        aiohttp_session.loop.run_until_complete(obj._request("GET", "url", {}))


def test_request_client_error(aiohttp_session):
    """Test the api request client error."""
    obj = base.BaseApiObject(None, client_session=aiohttp_session)

    @asyncio.coroutine
    def side_effect(*args, **kwargs):
        raise aiohttp.client_exceptions.ClientError()

    aiohttp_session.request.side_effect = side_effect

    with pytest.raises(exceptions.TransportError):
        aiohttp_session.loop.run_until_complete(obj._request("GET", "url", {}))


def test_request_status_error(aiohttp_session):
    """Test the api request client error."""
    obj = base.BaseApiObject(None, client_session=aiohttp_session)
    resp = AsyncMock()
    resp.status = 500
    resp.json.return_value = {
        "error": "mock_error"
    }
    aiohttp_session.request.return_value = resp

    with pytest.raises(exceptions.InternalError):
        aiohttp_session.loop.run_until_complete(obj._request("GET", "url", {}))


def test_request_status_parse_error(aiohttp_session):
    """Test the api request client error."""
    obj = base.BaseApiObject(None, client_session=aiohttp_session)
    resp = AsyncMock()
    resp.status = 500

    def side_effect(*args, **kwargs):
        raise ValueError()
    resp.json.side_effect = side_effect
    aiohttp_session.request.return_value = resp

    with pytest.raises(exceptions.InternalError):
        aiohttp_session.loop.run_until_complete(obj._request("GET", "url", {}))


def test_request_status_bad_json(aiohttp_session):
    """Test the api request client error."""
    obj = base.BaseApiObject(None, client_session=aiohttp_session)
    resp = AsyncMock()
    resp.status = 200

    def side_effect(*args, **kwargs):
        raise ValueError()
    resp.json.side_effect = side_effect
    aiohttp_session.request.return_value = resp

    with pytest.raises(exceptions.InvalidResponseError):
        aiohttp_session.loop.run_until_complete(obj._request("GET", "url", {}))
