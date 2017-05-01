"""Client interface for aioautomatic."""

import asyncio
import itertools
import json
import logging
import time

import aiohttp
from aiohttp import ClientError
from aiohttp.http_exceptions import HttpProcessingError

from aioautomatic import base
from aioautomatic import const
from aioautomatic import exceptions
from aioautomatic import session
from aioautomatic.const import EVENT_WS_ERROR, EVENT_WS_CLOSED
from aioautomatic.data import REALTIME_EVENT_CLASS
from aioautomatic.socketio import (
    decode_engineIO_content, ATTR_SESSION_ID, ATTR_PING_TIMEOUT,
    ATTR_PING_INTERVAL, ATTR_PING_TIMEOUT_HANDLE, ATTR_PING_INTERVAL_HANDLE)
from aioautomatic import validation

_LOGGER = logging.getLogger(__name__)

VALID_CALLBACKS = tuple(itertools.chain(
    (EVENT_WS_ERROR, EVENT_WS_CLOSED), REALTIME_EVENT_CLASS))


class Client(base.BaseApiObject):
    """API client object to access all underlying methods."""

    def __init__(self, client_id, client_secret, client_session=None,
                 request_kwargs=None):
        """Create a client object.

        :param client_id: Automatic Application Client ID
        :param client_secret: Automatic Application Secret
        :param client_session: aiohttp client session to be used for
                               lifetime of the object
        :param request_kwargs: kwargs to be sent with all aiohttp
                               requests
        :returns Client: Automatic API Client.
        """
        super().__init__(None, request_kwargs, client_session)
        self._client_id = client_id
        self._client_secret = client_secret
        self._ws_connection = None
        self._ws_session_data = None
        self._ws_callbacks = {k: [] for k in VALID_CALLBACKS}

    @asyncio.coroutine
    def create_session_from_password(self, scope, username, password):
        """Create a session object authenticated by username and password.

        :param scope: Requested API scope for this session
        :param username: User's Automatic account username
        :param username: User's Automatic account password
        :returns Session: Authenticated session object
        """
        _LOGGER.info("Creating session from username/password.")
        auth_payload = {
            'client_id': self._client_id,
            'client_secret': self._client_secret,
            'grant_type': 'password',
            'username': username,
            'password': password,
            'scope': ' '.join('scope:{}'.format(item) for item in scope),
            }
        resp = yield from self._post(const.AUTH_URL, auth_payload)
        data = validation.AUTH_TOKEN(resp)
        return session.Session(self, **data)

    @asyncio.coroutine
    def _get_engineio_session(self):
        """Connect to server and get an engineIO session."""
        # Automatic's websocket API is built on top of the engineIO API.
        # We have to first open an engineIO session before we can open the
        # websocket connection.
        params = {
            'EIO': 3,
            'transport': 'polling',
            'token': '{}:{}'.format(self.client_id, self.client_secret),
            't': '{}-0'.format(time.time()),
        }
        url = const.WEBSOCKET_SESSION_URL.format(
            '&'.join('{}={}'.format(k, v) for k, v in params.items()))
        resp = yield from self._raw_request(aiohttp.hdrs.METH_GET, url)
        data = yield from resp.read()
        packet_type, packet_data = next(decode_engineIO_content(data))
        packet_str = packet_data.decode('utf-8')
        if packet_type != 0:
            raise exceptions.TransportError(
                'engineIO packet is not open type: {}'.format(packet_str))
        session_data = json.loads(packet_str)

        # Convert from ms to seconds
        session_data[ATTR_PING_TIMEOUT] /= 1000.0
        session_data[ATTR_PING_INTERVAL] /= 1000.0

        return session_data

    @asyncio.coroutine
    def _get_ws_connection(self, session_data):
        """Open a websocket connection with an engineIO session."""
        params = {
            'EIO': 3,
            'transport': 'websocket',
            'token': '{}:{}'.format(self.client_id, self.client_secret),
            'sid': session_data[ATTR_SESSION_ID],
        }
        url = const.WEBSOCKET_URL.format(
            '&'.join('{}={}'.format(k, v) for k, v in params.items()))
        ws_connection = yield from self._client_session.ws_connect(
            url, timeout=session_data['pingTimeout'])

        # Send engineIO probe message
        yield from ws_connection.send_str('2probe')
        resp = yield from ws_connection.receive_str()
        if resp != '3probe':
            raise exceptions.ProtocolError(
                'engineIO probe response packet not received: {}'.format(resp))

        # Send engineIO connection upgrade packet
        yield from ws_connection.send_str('5')
        resp = yield from ws_connection.receive_str()
        if resp != '40':
            if resp.startswith('44'):
                try:
                    # If a valid message was sent, raise the appropriate error
                    msg = json.loads(resp[2:])
                    raise exceptions.get_socketio_error(msg)
                except ValueError:
                    pass
            raise exceptions.ProtocolError(
                'socketIO connect packet not received: {}'.format(resp))

        return ws_connection

    @asyncio.coroutine
    def ws_connect(self):
        """Open a websocket connection for real time events."""
        if self.ws_connected:
            raise exceptions.TransportError('Connection already open.')

        _LOGGER.info("Opening websocket connection.")
        try:
            # Open an engineIO session
            session_data = yield from self._get_engineio_session()

            # Now that the session data has been fetched, open the actual
            # websocket connection.
            ws_connection = yield from self._get_ws_connection(session_data)

            # Finalize connection status
            self._ws_connection = ws_connection
            self._ws_session_data = session_data

            # Send the first ping packet
            self.loop.create_task(self._ping())
        except (ClientError, HttpProcessingError, asyncio.TimeoutError) as exc:
            raise exceptions.TransportError from exc
        return self.loop.create_task(self._ws_loop())

    @asyncio.coroutine
    def _ping(self):
        """Send the ping packet and wait for a response."""
        yield from self._ws_connection.send_str('2')

        handle = self._ws_session_data.get(ATTR_PING_TIMEOUT_HANDLE)
        if handle:
            handle.cancel()

        self._ws_session_data[ATTR_PING_TIMEOUT_HANDLE] = self.loop.call_later(
            self._ws_session_data[ATTR_PING_TIMEOUT],
            lambda: self.loop.create_task(self.ws_close()))

    def _handle_packet(self, data):
        """Handle an incoming engineIO packet."""
        # engineIO Ping response received. Schedule next ping.
        if data == '3':
            handle = self._ws_session_data.get(ATTR_PING_INTERVAL_HANDLE)
            if handle:
                handle.cancel()

            self._ws_session_data[ATTR_PING_INTERVAL_HANDLE] = \
                self.loop.call_later(
                    self._ws_session_data[ATTR_PING_INTERVAL],
                    lambda: self.loop.create_task(self._ping()))
            return

        # socketIO event
        if data.startswith('42'):
            msg = json.loads(data[2:])
            name = msg[0]
            event = msg[1]

            event_class = REALTIME_EVENT_CLASS.get(name)
            if event_class is None:
                _LOGGER.error('Invalid event %s received from Automatic', name)
                _LOGGER.debug(event)
                return

            self._handle_event(name, event_class(self, event))
            return

        # socketIO error
        if data.startswith('44'):
            msg = json.loads(data[2:])
            self._handle_event(EVENT_WS_ERROR, msg)
            return

        _LOGGER.debug('Unhandled packet %s', data)

    def _handle_event(self, name, event):
        """Handle an incoming realtime event object."""
        for callback in self._ws_callbacks[name]:
            self.loop.call_soon(callback, name, event)

    @asyncio.coroutine
    def _ws_loop(self):
        """Run the websocket loop listening for messages."""
        msg = None
        try:
            while True:
                msg = yield from self._ws_connection.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    self._handle_packet(msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
        except (ClientError, HttpProcessingError, asyncio.TimeoutError) as exc:
            raise exceptions.TransportError from exc
        finally:
            yield from self.ws_close()
            self._handle_event(EVENT_WS_CLOSED, None)
            if msg is not None and msg.type == aiohttp.WSMsgType.ERROR:
                raise exceptions.TransportError(
                    'Websocket error detected. Connection closed.')

    @asyncio.coroutine
    def ws_close(self):
        """Close the websocket connection."""
        if not self.ws_connected:
            return

        # Try to gracefully end the connection
        try:
            yield from self._ws_connection.send_str('41')
            yield from self._ws_connection.send_str('1')
        except (ClientError, HttpProcessingError, asyncio.TimeoutError):
            pass

        # Close any remaining ping handles
        handle = self._ws_session_data.get(ATTR_PING_INTERVAL_HANDLE)
        if handle:
            handle.cancel()
        handle = self._ws_session_data.get(ATTR_PING_TIMEOUT_HANDLE)
        if handle:
            handle.cancel()

        yield from self._ws_connection.close()
        self._ws_connection = None
        self._ws_session_data = None

    def on(self, event, callback):  # pylint: disable=invalid-name
        """Register a callback to be run on a websocket event.

        Valid realtime events can be found in Automatic's documentation.
        In addition, the events "error" and "closed" can be registered.
        "error" will be called if an error is sent from Automatic's
        servers via websocket. "closed" will be called once when the
        websocket connection is closed.

        The callback must accept two positional parameters. The first
        contians the name of the event triggering  the callback. The
        second contains the event data. For realtime events, this will
        contain a subclass of aioautomatic.data.BaseRealtimeEvent. An
        "error" callback will pass a string containing the data received
        from Automatic, and "closed" will pass None.

        https://developer.automatic.com/api-reference/#real-time-events

        :param event: Realtime event to trigger the callback
        :param callback: Callback to be run when the event occurs
        :returns remove: Callable to unregister this callback
        """
        if event not in VALID_CALLBACKS:
            raise ValueError(
                '{} is not a valid callback. Valid callbacks are {}'.format(
                    event, VALID_CALLBACKS))

        self._ws_callbacks[event].append(callback)

        def remove_callable():
            """Callable to remove the registered callback."""
            self._ws_callbacks[event].remove(callback)

        return remove_callable

    def on_app_event(self, callback):
        """Register a callback to be run on all Automatic events.

        This is a helper function that wraps Client.on. The callback
        passed here will be registered for all vehicle status events
        sent from Automatic. It will not be registered for "error" or
        "closed" events.

        The callback must accept two positional parameters. The first
        contians the name of the event triggering  the callback. The
        second contains the event data. This will contain a subclass of
        aioautomatic.data.BaseRealtimeEvent.

        :param callback: Callback to be run when an event occurs
        :returns remove: Callable to unregister this callback
        """
        removes = []
        for event in REALTIME_EVENT_CLASS:
            removes.append(self.on(event, callback))

        def remove_callable():
            """Callable to remove the registered callback."""
            for remove in removes:
                remove()

        return remove_callable

    @property
    def ws_connected(self):
        """Websocket is connected."""
        return self._ws_connection is not None

    @property
    def client_id(self):
        """Automatic Application Client ID"""
        return self._client_id

    @property
    def client_secret(self):
        """Automatic Application Secret"""
        return self._client_secret
