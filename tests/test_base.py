"""Tests for automatic base objects."""
import asyncio
import aiohttp
import voluptuous as vol
from aioautomatic import base
from aioautomatic import exceptions

import pytest
from unittest.mock import patch
from tests.common import AsyncMock


class MockDataObject(base.BaseDataObject):
    validator = vol.Schema({"attr1": str}, extra=vol.REMOVE_EXTRA)


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


def test_base_data_object_no_validator():
    """Test the base data object with no validator."""
    obj = base.BaseDataObject({
        "attr1": "value1",
        "attr2": "value2",
    })
    with pytest.raises(AttributeError):
        obj.attr1


def test_base_data_object():
    """Test the base data object."""
    obj = MockDataObject({
        "attr1": "value1",
        "attr2": "value2",
    })

    assert obj.attr1 == "value1"
    with pytest.raises(AttributeError):
        obj.attr2
    with pytest.raises(AttributeError):
        obj.attr3


def test_result_list(session):
    """Test the result object."""
    obj = base.ResultList(parent=session, item_class=MockDataObject, resp={
        "_metadata": {
            "count": 2,
            "next": None,
            "previous": None,
            },
        "results": [
            {
                "attr1": "value1",
                "attr2": "value2",
            }, {
                "attr1": "value3"
            }],
        })
    next_list = session.loop.run_until_complete(obj.get_next())
    previous_list = session.loop.run_until_complete(obj.get_previous())
    assert obj.next is None
    assert obj.previous is None
    assert next_list is None
    assert previous_list is None
    assert len(obj) == 2
    assert sorted([item.attr1 for item in obj]) == sorted(["value1", "value3"])


def test_result_next_list(session):
    """Test the result object get next list."""
    obj = base.ResultList(parent=session, item_class=MockDataObject, resp={
        "_metadata": {
            "count": 0,
            "next": "next_url",
            "previous": None,
            },
        "results": [],
        })
    resp = AsyncMock()
    resp.status = 200
    mock_json = {
        "_metadata": {
            "count": 2,
            "next": None,
            "previous": None,
            },
        "results": [
            {
                "attr1": "value1",
                "attr2": "value2",
            }, {
                "attr1": "value3"
            }],
    }
    resp.json.return_value = mock_json
    session._client_session.request.return_value = resp

    next_list = session.loop.run_until_complete(obj.get_next())
    previous_list = session.loop.run_until_complete(obj.get_previous())
    assert obj.previous is None
    assert previous_list is None
    assert len(obj) == 0

    assert obj.next is "next_url"
    assert len(obj) == 0
    assert len(next_list) == 2
    assert sorted([item.attr1 for item in next_list]) == \
        sorted(["value1", "value3"])


def test_result_previous_list(session):
    """Test the result object get previous list."""
    obj = base.ResultList(parent=session, item_class=MockDataObject, resp={
        "_metadata": {
            "count": 0,
            "next": None,
            "previous": "previous_url",
            },
        "results": [],
        })
    resp = AsyncMock()
    resp.status = 200
    mock_json = {
        "_metadata": {
            "count": 2,
            "next": None,
            "previous": None,
            },
        "results": [
            {
                "attr1": "value1",
                "attr2": "value2",
            }, {
                "attr1": "value3"
            }],
    }
    resp.json.return_value = mock_json
    session._client_session.request.return_value = resp

    next_list = session.loop.run_until_complete(obj.get_next())
    previous_list = session.loop.run_until_complete(obj.get_previous())
    assert obj.next is None
    assert next_list is None
    assert len(obj) == 0

    assert obj.previous is "previous_url"
    assert len(obj) == 0
    assert len(previous_list) == 2
    assert sorted([item.attr1 for item in previous_list]) == \
        sorted(["value1", "value3"])
