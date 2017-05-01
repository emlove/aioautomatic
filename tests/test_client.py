"""Tests for automatic client."""
import asyncio
import json
import queue

from aioautomatic.client import Client
from aioautomatic import data
from aioautomatic import exceptions
import aiohttp

import pytest
from tests.common import AsyncMock
from unittest.mock import patch, MagicMock


def test_create_client(aiohttp_session):
    """Create a client object."""
    client_id = 'mock_id'
    client_secret = 'mock_secret'
    client = Client(client_id, client_secret, aiohttp_session)
    assert client.client_id == client_id
    assert client.client_secret == client_secret


def test_create_session_from_password(client):
    """Test opening a session from the users password."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "access_token": "mock_access",
        "expires_in": 123456,
        "scope": ("scope:location scope:vehicle:profile "
                  "scope:user:profile scope:trip"),
        "refresh_token": "mock_refresh",
        "token_type": "Bearer",
    }
    client._client_session.request.return_value = resp

    client.loop.run_until_complete(
        client.create_session_from_password(
            ['location', 'trip'], "mock_user", "mock_pass"))
    assert client._client_session.request.called
    assert len(client._client_session.request.mock_calls) == 2
    assert client._client_session.request.mock_calls[0][1][0] == "POST"
    assert client._client_session.request.mock_calls[0][1][1] == \
        "https://accounts.automatic.com/oauth/access_token"
    assert client._client_session.request.mock_calls[0][2]['data'] == {
        "client_id": client.client_id,
        "client_secret": client.client_secret,
        "grant_type": "password",
        "username": "mock_user",
        "password": "mock_pass",
        "scope": ("scope:location scope:trip"),
    }


def test_scope_forbidden(client):
    """Test opening a session from the users password."""
    resp = AsyncMock()
    resp.status = 403
    resp.json.return_value = {
        "error": "access_denied",
    }
    client._client_session.request.return_value = resp

    with pytest.raises(exceptions.ForbiddenError):
        client.loop.run_until_complete(client.create_session_from_password(
            ['location', 'trip'], "mock_user", "mock_pass"))


@patch('time.time', return_value=1493426946.123)
def test_get_engineio_session(mock_time, client):
    """Test requesting an engineIO session from Automatic."""
    resp = AsyncMock()
    resp.status = 200
    data = json.dumps({
        "sid": "mock_session_id",
        "pingTimeout": 12345,
        "pingInterval": 23456,
    }).encode('utf-8')
    length_str = str(len(data)).encode('utf-8')

    # Build engineIO session create packet
    resp.read.return_value = \
        b'\x01\x00' + length_str + b'\xFF\xFF0' + data
    client._client_session.request.return_value = resp

    session_data = client.loop.run_until_complete(
        client._get_engineio_session())
    assert client._client_session.request.called
    assert len(client._client_session.request.mock_calls) == 2
    assert client._client_session.request.mock_calls[0][1][0] == "GET"
    assert client._client_session.request.mock_calls[0][1][1][:40] == \
        "https://stream.automatic.com/socket.io/?"
    query = client._client_session.request.mock_calls[0][1][1][40:].split('&')
    params = {}
    for item in query:
        k, v = item.split('=')
        params[k] = v
    assert params == {
        "EIO": "3",
        "token": "mock_id:mock_secret",
        "transport": "polling",
        "t": "1493426946.123-0",
    }
    assert session_data == {
        "sid": "mock_session_id",
        "pingTimeout": 12.345,
        "pingInterval": 23.456,
    }


@patch('time.time', return_value=1493426946.123)
def test_get_engineio_session_error(mock_time, client):
    """Test error requesting an engineIO session from Automatic."""
    resp = AsyncMock()
    resp.status = 200
    data = 'Error Requesting Session'.encode('utf-8')
    length_str = str(len(data)).encode('utf-8')

    # Build engineIO session create packet
    resp.read.return_value = \
        b'\x01\x00' + length_str + b'\xFF\xFF4' + data
    client._client_session.request.return_value = resp

    with pytest.raises(exceptions.TransportError) as exc:
        client.loop.run_until_complete(
            client._get_engineio_session())

    assert str(exc.value) == \
        "engineIO packet is not open type: Error Requesting Session"


def test_get_ws_connection(client):
    """Test opening a websocket connection with an engineIO session."""
    mock_ws = AsyncMock()
    receive_queue = asyncio.Queue(loop=client.loop)
    mock_ws.receive_str = receive_queue.get

    @asyncio.coroutine
    def mock_send_str(data):
        if data == "2probe":
            yield from receive_queue.put("3probe")
            return

        if data == "5":
            yield from receive_queue.put("40")

    mock_ws.send_str = mock_send_str
    client._client_session.ws_connect.return_value = mock_ws
    session_data = {
        "sid": "mock_session_id",
        "pingTimeout": 12.345,
        "pingInterval": 23.456,
    }
    client.loop.run_until_complete(
        client._get_ws_connection(session_data))
    assert client._client_session.ws_connect.called
    assert len(client._client_session.ws_connect.mock_calls) == 1
    assert client._client_session.ws_connect.mock_calls[0][1][0][:38] == \
        "wss://stream.automatic.com/socket.io/?"
    query = \
        client._client_session.ws_connect.mock_calls[0][1][0][38:].split('&')
    params = {}
    for item in query:
        k, v = item.split('=')
        params[k] = v
    assert params == {
        "EIO": "3",
        "token": "mock_id:mock_secret",
        "transport": "websocket",
        "sid": "mock_session_id",
    }


def test_get_ws_connection_probe_error(client):
    """Test error opening a websocket connection with an engineIO session."""
    mock_ws = AsyncMock()
    receive_queue = asyncio.Queue(loop=client.loop)
    mock_ws.receive_str = receive_queue.get

    @asyncio.coroutine
    def mock_send_str(data):
        if data == "2probe":
            yield from receive_queue.put("4Probe Error")
            return

        if data == "5":
            yield from receive_queue.put("40")

    mock_ws.send_str = mock_send_str
    client._client_session.ws_connect.return_value = mock_ws
    session_data = {
        "sid": "mock_session_id",
        "pingTimeout": 12.345,
        "pingInterval": 23.456,
    }
    with pytest.raises(exceptions.ProtocolError) as exc:
        client.loop.run_until_complete(
            client._get_ws_connection(session_data))

    assert str(exc.value) == \
        "engineIO probe response packet not received: 4Probe Error"


def test_get_ws_connection_unauthorized_client(client):
    """Test error opening a websocket connection with an engineIO session."""
    mock_ws = AsyncMock()
    receive_queue = asyncio.Queue(loop=client.loop)
    mock_ws.receive_str = receive_queue.get

    @asyncio.coroutine
    def mock_send_str(data):
        if data == "2probe":
            yield from receive_queue.put("3probe")
            return

        if data == "5":
            yield from receive_queue.put('44"Unauthorized client."')

    mock_ws.send_str = mock_send_str
    client._client_session.ws_connect.return_value = mock_ws
    session_data = {
        "sid": "mock_session_id",
        "pingTimeout": 12.345,
        "pingInterval": 23.456,
    }
    with pytest.raises(exceptions.UnauthorizedClientError) as exc:
        client.loop.run_until_complete(
            client._get_ws_connection(session_data))

    assert str(exc.value) == "Unauthorized client."


def test_get_ws_connection_upgrade_error(client):
    """Test error opening a websocket connection with an engineIO session."""
    mock_ws = AsyncMock()
    receive_queue = asyncio.Queue(loop=client.loop)
    mock_ws.receive_str = receive_queue.get

    @asyncio.coroutine
    def mock_send_str(data):
        if data == "2probe":
            yield from receive_queue.put("3probe")
            return

        if data == "5":
            yield from receive_queue.put('44"socketIO Mock Error"')

    mock_ws.send_str = mock_send_str
    client._client_session.ws_connect.return_value = mock_ws
    session_data = {
        "sid": "mock_session_id",
        "pingTimeout": 12.345,
        "pingInterval": 23.456,
    }
    with pytest.raises(exceptions.SocketIOError) as exc:
        client.loop.run_until_complete(
            client._get_ws_connection(session_data))

    assert str(exc.value) == "socketIO Mock Error"


def test_get_ws_connection_invalid_error(client):
    """Test error opening a websocket connection with an engineIO session."""
    mock_ws = AsyncMock()
    receive_queue = asyncio.Queue(loop=client.loop)
    mock_ws.receive_str = receive_queue.get

    @asyncio.coroutine
    def mock_send_str(data):
        if data == "2probe":
            yield from receive_queue.put("3probe")
            return

        if data == "5":
            yield from receive_queue.put('44[[[')

    mock_ws.send_str = mock_send_str
    client._client_session.ws_connect.return_value = mock_ws
    session_data = {
        "sid": "mock_session_id",
        "pingTimeout": 12.345,
        "pingInterval": 23.456,
    }
    with pytest.raises(exceptions.ProtocolError):
        client.loop.run_until_complete(
            client._get_ws_connection(session_data))


def test_get_ws_connection_invalid_packet(client):
    """Test error opening a websocket connection with an engineIO session."""
    mock_ws = AsyncMock()
    receive_queue = asyncio.Queue(loop=client.loop)
    mock_ws.receive_str = receive_queue.get

    @asyncio.coroutine
    def mock_send_str(data):
        if data == "2probe":
            yield from receive_queue.put("3probe")
            return

        if data == "5":
            yield from receive_queue.put('ABCDEF')

    mock_ws.send_str = mock_send_str
    client._client_session.ws_connect.return_value = mock_ws
    session_data = {
        "sid": "mock_session_id",
        "pingTimeout": 12.345,
        "pingInterval": 23.456,
    }
    with pytest.raises(exceptions.ProtocolError):
        client.loop.run_until_complete(
            client._get_ws_connection(session_data))


def test_ws_connect(client):
    """Test websocket connect and ping loop."""
    mock_ws = AsyncMock()
    send_queue = queue.Queue()
    receive_queue = asyncio.Queue(loop=client.loop)
    mock_ws.receive = receive_queue.get

    @asyncio.coroutine
    def mock_send_str(data):
        send_queue.put(data)

    mock_ws.send_str = mock_send_str

    session_data = {
        "sid": "mock_session_id",
        "pingTimeout": 12.345,
        "pingInterval": 23.456,
    }
    client._get_engineio_session = AsyncMock()
    client._get_engineio_session.return_value = session_data
    client._get_ws_connection = AsyncMock()
    client._get_ws_connection.return_value = mock_ws

    ws_loop = client.loop.run_until_complete(client.ws_connect())
    assert not ws_loop.done()

    packet = send_queue.get(False)
    assert send_queue.empty()
    assert packet == "2"

    msg = MagicMock()
    msg.type = aiohttp.WSMsgType.CLOSED
    client.loop.run_until_complete(receive_queue.put(msg))
    assert ws_loop.done()

    packet = send_queue.get(False)
    assert packet == "41"
    packet = send_queue.get(False)
    assert packet == "1"
    assert send_queue.empty()
    assert mock_ws.close.called
    assert len(mock_ws.close.mock_calls) == 1


def test_ws_connect_timeout(client):
    """Test websocket connect timeout."""
    @asyncio.coroutine
    def get_session():
        raise asyncio.TimeoutError("Session Timeout Error")
    client._get_engineio_session = get_session

    with pytest.raises(exceptions.TransportError):
        client.loop.run_until_complete(client.ws_connect())


def test_ws_double_connect_timeout(client):
    """Test double websocket connect exception."""
    client._ws_connection = AsyncMock()
    with pytest.raises(exceptions.TransportError):
        client.loop.run_until_complete(client.ws_connect())


def test_ws_ping(client):
    """Test websocket ping."""
    mock_ws = AsyncMock()
    send_queue = queue.Queue()
    receive_queue = asyncio.Queue(loop=client.loop)
    mock_ws.receive = receive_queue.get

    @asyncio.coroutine
    def mock_send_str(data):
        send_queue.put(data)

    mock_ws.send_str = mock_send_str

    old_handle = MagicMock()
    client.ws_close = AsyncMock()
    client.loop.call_later = MagicMock()
    client._ws_connection = mock_ws
    client._ws_session_data = {
        "sid": "mock_session_id",
        "pingTimeout": 12.345,
        "pingInterval": 23.456,
        "pingTimeoutHandle": old_handle,
    }
    client.loop.run_until_complete(client._ping())

    packet = send_queue.get(False)
    assert send_queue.empty()
    assert packet == "2"

    assert old_handle.cancel.called
    assert len(old_handle.cancel.mock_calls) == 1

    assert client.loop.call_later.called
    assert len(client.loop.call_later.mock_calls) == 1
    assert client.loop.call_later.mock_calls[0][1][0] == 12.345
    timeout = client.loop.call_later.mock_calls[0][1][1]
    assert not client.ws_close.called
    future = timeout()
    client.loop.run_until_complete(future)
    assert client.ws_close.called
    assert len(client.ws_close.mock_calls) == 1


def test_ws_handle_first_ping(client):
    """Test websocket ping."""
    client._ping = AsyncMock()
    client.loop.call_later = MagicMock()
    client._ws_session_data = {
        "sid": "mock_session_id",
        "pingTimeout": 12.345,
        "pingInterval": 23.456,
    }
    client._handle_packet('3')

    assert client.loop.call_later.called
    assert len(client.loop.call_later.mock_calls) == 1
    assert client.loop.call_later.mock_calls[0][1][0] == 23.456
    interval = client.loop.call_later.mock_calls[0][1][1]
    assert not client._ping.called
    future = interval()
    client.loop.run_until_complete(future)
    assert client._ping.called
    assert len(client._ping.mock_calls) == 1


def test_ws_handle_next_ping(client):
    """Test websocket ping."""
    old_handle = MagicMock()
    client._ping = AsyncMock()
    client.loop.call_later = MagicMock()
    client._ws_session_data = {
        "sid": "mock_session_id",
        "pingTimeout": 12.345,
        "pingInterval": 23.456,
        "pingIntervalHandle": old_handle,
    }
    client._handle_packet('3')

    assert old_handle.cancel.called
    assert len(old_handle.cancel.mock_calls) == 1

    assert client.loop.call_later.called
    assert len(client.loop.call_later.mock_calls) == 1
    assert client.loop.call_later.mock_calls[0][1][0] == 23.456
    interval = client.loop.call_later.mock_calls[0][1][1]
    assert not client._ping.called
    future = interval()
    client.loop.run_until_complete(future)
    assert client._ping.called
    assert len(client._ping.mock_calls) == 1


@patch('aioautomatic.client._LOGGER')
def test_ws_handle_invalid_event(mock_logger, client):
    """Test websocket invalid event."""
    client._handle_event = MagicMock()
    client._handle_packet('42{}'.format(json.dumps([
        "invalid_event",
        "event_msg",
    ])))

    assert not client._handle_event.called

    assert mock_logger.error.called
    assert len(mock_logger.error.mock_calls) == 1
    assert mock_logger.error.mock_calls[0][1][0] == \
        "Invalid event %s received from Automatic"
    assert mock_logger.error.mock_calls[0][1][1] == "invalid_event"

    assert mock_logger.debug.called
    assert len(mock_logger.debug.mock_calls) == 1
    assert mock_logger.debug.mock_calls[0][1][0] == "event_msg"


def test_ws_handle_valid_event(client):
    """Test websocket valid event."""
    client._handle_event = MagicMock()
    client._handle_packet('42{}'.format(json.dumps([
        "location:updated",
        {
            "id": "mock_id",
            "user": {
                "id": "mock_user_id",
                "url": "mock_user_url",
            },
            "type": "location:updated",
            "vehicle": {
                "id": "mock_vehicle_id",
                "url": "mock_vehicle_url",
            },
            "device": {
                "id": "mock_device_id",
            },
        },
    ])))

    assert client._handle_event.called
    assert len(client._handle_event.mock_calls) == 1
    assert client._handle_event.mock_calls[0][1][0] == "location:updated"
    event = client._handle_event.mock_calls[0][1][1]
    assert type(event) is data.RealtimeLocationUpdated
    assert event.id == "mock_id"
    assert event.type == "location:updated"
    assert event.user.id == "mock_user_id"
    assert event.user.url == "mock_user_url"
    assert event.vehicle.id == "mock_vehicle_id"
    assert event.vehicle.url == "mock_vehicle_url"
    assert event.device.id == "mock_device_id"


def test_ws_handle_socketio_error(client):
    """Test websocket socketio error event."""
    client._handle_event = MagicMock()
    client._handle_packet('44"Error Message"')

    assert client._handle_event.called
    assert len(client._handle_event.mock_calls) == 1
    assert client._handle_event.mock_calls[0][1][0] == "error"
    assert client._handle_event.mock_calls[0][1][1] == "Error Message"


@patch('aioautomatic.client._LOGGER')
def test_ws_handle_socketio_unknown_packet(mock_logger, client):
    """Test websocket socketio error event."""
    client._handle_event = MagicMock()
    client._handle_packet('Transport Error')

    assert not client._handle_event.called
    assert mock_logger.debug.called
    assert len(mock_logger.debug.mock_calls) == 1
    assert mock_logger.debug.mock_calls[0][1][0] == "Unhandled packet %s"
    assert mock_logger.debug.mock_calls[0][1][1] == "Transport Error"


def test_ws_loop_messages(client):
    """Test websocket loop messages received."""
    mock_ws = AsyncMock()
    receive_queue = asyncio.Queue(loop=client.loop)
    mock_ws.receive = receive_queue.get

    client._ws_connection = mock_ws
    client.ws_close = AsyncMock()
    client._handle_packet = MagicMock()

    msg = MagicMock()
    msg.type = aiohttp.WSMsgType.TEXT
    msg.data = 'mock message 1'
    client.loop.run_until_complete(receive_queue.put(msg))
    msg = MagicMock()
    msg.type = aiohttp.WSMsgType.TEXT
    msg.data = 'mock message 2'
    client.loop.run_until_complete(receive_queue.put(msg))
    msg = MagicMock()
    msg.type = aiohttp.WSMsgType.BINARY
    msg.data = b'binary message to be ignored'
    client.loop.run_until_complete(receive_queue.put(msg))
    msg = MagicMock()
    msg.type = aiohttp.WSMsgType.CLOSED
    client.loop.run_until_complete(receive_queue.put(msg))

    client.loop.run_until_complete(client._ws_loop())

    assert client._handle_packet.called
    assert len(client._handle_packet.mock_calls) == 2
    assert client._handle_packet.mock_calls[0][1][0] == 'mock message 1'
    assert client._handle_packet.mock_calls[1][1][0] == 'mock message 2'


def test_ws_loop_error(client):
    """Test websocket loop error message."""
    mock_ws = AsyncMock()
    receive_queue = asyncio.Queue(loop=client.loop)
    mock_ws.receive = receive_queue.get

    client._ws_connection = mock_ws
    client.ws_close = AsyncMock()
    client._handle_event = MagicMock()

    msg = MagicMock()
    msg.type = aiohttp.WSMsgType.ERROR
    client.loop.run_until_complete(receive_queue.put(msg))

    with pytest.raises(exceptions.TransportError) as exc:
        client.loop.run_until_complete(client._ws_loop())

    assert client.ws_close.called
    assert len(client.ws_close.mock_calls) == 1
    assert client._handle_event.called
    assert len(client._handle_event.mock_calls) == 1
    assert client._handle_event.mock_calls[0][1][0] == 'closed'
    assert client._handle_event.mock_calls[0][1][1] is None
    assert str(exc.value) == "Websocket error detected. Connection closed."


def test_ws_loop_exception(client):
    """Test websocket loop exception."""
    @asyncio.coroutine
    def side_effect(*args, **kwargs):
        raise aiohttp.ClientError("Mock Exception")
    mock_ws = AsyncMock()
    mock_ws.receive.side_effect = side_effect

    client._ws_connection = mock_ws
    client.ws_close = AsyncMock()
    client._handle_event = MagicMock()

    with pytest.raises(exceptions.TransportError):
        client.loop.run_until_complete(client._ws_loop())

    assert client.ws_close.called
    assert len(client.ws_close.mock_calls) == 1
    assert client._handle_event.called
    assert len(client._handle_event.mock_calls) == 1
    assert client._handle_event.mock_calls[0][1][0] == 'closed'
    assert client._handle_event.mock_calls[0][1][1] is None


def test_ws_close(client):
    """Test websocket close."""
    mock_ws = AsyncMock()
    interval_mock = MagicMock()
    timeout_mock = MagicMock()

    client._ws_connection = mock_ws
    client._ws_session_data = {
        'pingIntervalHandle': interval_mock,
        'pingTimeoutHandle': timeout_mock,
    }

    client.loop.run_until_complete(client.ws_close())

    assert mock_ws.close.called
    assert len(mock_ws.close.mock_calls) == 1
    assert mock_ws.send_str.called
    assert len(mock_ws.send_str.mock_calls) == 2
    assert mock_ws.send_str.mock_calls[0][1][0] == '41'
    assert mock_ws.send_str.mock_calls[1][1][0] == '1'
    assert interval_mock.cancel.called
    assert len(interval_mock.cancel.mock_calls) == 1
    assert timeout_mock.cancel.called
    assert len(timeout_mock.cancel.mock_calls) == 1


def test_ws_close_noop(client):
    """Test websocket close when already closed."""
    client.loop.run_until_complete(client.ws_close())


def test_ws_close_exception(client):
    """Test websocket close exception."""
    @asyncio.coroutine
    def side_effect(*args, **kwargs):
        raise aiohttp.ClientError("Mock Exception")
    mock_ws = AsyncMock()
    mock_ws.send_str.side_effect = side_effect

    client._ws_connection = mock_ws
    client._ws_session_data = {}
    client._handle_event = MagicMock()

    client.loop.run_until_complete(client.ws_close())

    assert mock_ws.close.called
    assert len(mock_ws.close.mock_calls) == 1
    assert mock_ws.send_str.called
    assert len(mock_ws.send_str.mock_calls) == 1
    assert mock_ws.send_str.mock_calls[0][1][0] == '41'


def test_on_invalid_event(client):
    """Test registration attempt to invalid event."""
    with pytest.raises(ValueError) as exc:
        client.on('invalid_event', None)

    assert str(exc.value)[:38] == 'invalid_event is not a valid callback.'


def test_on_event(client):
    """Test event handler registration and removal."""
    mock_calls = []

    def callback(event, data):
        """Mock callback."""
        mock_calls.append((event, data))

    remove = client.on('location:updated', callback)

    client._handle_event('location:updated', 'mock_data_1')
    tasks = asyncio.Task.all_tasks(client.loop)
    client.loop.run_until_complete(asyncio.gather(*tasks, loop=client.loop))
    assert len(mock_calls) == 1
    assert mock_calls[0] == ('location:updated', 'mock_data_1')
    mock_calls = []

    remove()

    client._handle_event('location:updated', 'mock_data_1')
    tasks = asyncio.Task.all_tasks(client.loop)
    client.loop.run_until_complete(asyncio.gather(*tasks, loop=client.loop))
    assert len(mock_calls) == 0


def test_on_app_event(client):
    """Test app event handler registration and removal."""
    mock_calls = []

    def callback(event, data):
        """Mock callback."""
        mock_calls.append((event, data))

    remove = client.on_app_event(callback)

    client._handle_event('location:updated', 'mock_data_1')
    tasks = asyncio.Task.all_tasks(client.loop)
    client.loop.run_until_complete(asyncio.gather(*tasks, loop=client.loop))
    assert len(mock_calls) == 1
    assert mock_calls[0] == ('location:updated', 'mock_data_1')
    mock_calls = []

    client._handle_event('notification:speeding', 'mock_data_2')
    tasks = asyncio.Task.all_tasks(client.loop)
    client.loop.run_until_complete(asyncio.gather(*tasks, loop=client.loop))
    assert len(mock_calls) == 1
    assert mock_calls[0] == ('notification:speeding', 'mock_data_2')
    mock_calls = []

    client._handle_event('closed', None)
    tasks = asyncio.Task.all_tasks(client.loop)
    client.loop.run_until_complete(asyncio.gather(*tasks, loop=client.loop))
    assert len(mock_calls) == 0
    mock_calls = []

    remove()

    client._handle_event('location:updated', 'mock_data_1')
    tasks = asyncio.Task.all_tasks(client.loop)
    client.loop.run_until_complete(asyncio.gather(*tasks, loop=client.loop))
    assert len(mock_calls) == 0

    client._handle_event('notification:speeding', 'mock_data_2')
    tasks = asyncio.Task.all_tasks(client.loop)
    client.loop.run_until_complete(asyncio.gather(*tasks, loop=client.loop))
    assert len(mock_calls) == 0
