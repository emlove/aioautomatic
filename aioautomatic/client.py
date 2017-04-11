"""Client interface for aioautomatic."""

import asyncio
import logging

import aiohttp

from aioautomatic import const
from aioautomatic import exceptions
from aioautomatic import session
from aioautomatic import validation

_LOGGER = logging.getLogger(__name__)


class Client():
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
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_session = client_session or aiohttp.ClientSession()
        self.loop = self.client_session.loop
        self.request_kwargs = request_kwargs or {}

    @asyncio.coroutine
    def create_session_from_password(self, username, password):
        """Create a session object authenticated by username and password.

        :param username: User's Automatic account username
        :param username: User's Automatic account password
        :returns Session: Authenticated session object
        """
        _LOGGER.info("Creating session from username/password.")
        auth_payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'password',
            'username': username,
            'password': password,
            'scope': const.FULL_SCOPE,
            }
        try:
            resp = yield from self.post(const.AUTH_URL, auth_payload)
        except exceptions.ForbiddenError:
            auth_payload['scope'] = const.DEFAULT_SCOPE
            resp = yield from self.post(const.AUTH_URL, auth_payload)
            _LOGGER.warning("No client access to scope:current_location. "
                            "Live location updates not available.")
        resp = validation.AUTH_TOKEN(resp)
        return session.Session(self, **resp)

    @asyncio.coroutine
    def request(self, method, url, data):
        """Wrapper for aiohttp request that returns a parsed dict."""
        try:
            _LOGGER.debug('Sending %s, to %s: %s', method, url, data)
            resp = yield from self.client_session.request(
                method, url, data=data, **self.request_kwargs)
        except (aiohttp.client_exceptions.ClientError,
                asyncio.TimeoutError) as exc:
            raise exceptions.TransportError from exc

        status_exception = exceptions.HTTP_EXCEPTIONS.get(resp.status)
        if status_exception is not None:
            resp_json = {}
            try:
                resp_json = yield from resp.json()
            except (aiohttp.client_exceptions.ClientResponseError,
                    ValueError):
                # Error message is nice, but not required
                pass
            raise status_exception(resp_json.get('error'),
                                   resp_json.get('error_description'))

        try:
            return (yield from resp.json())
        except (aiohttp.client_exceptions.ClientResponseError,
                ValueError) as exc:
            raise exceptions.ProtocolError from exc

    def get(self, url, data):
        """Wrapper for aiohttp get.

        This method is a coroutine.
        """
        return self.request(aiohttp.hdrs.METH_GET, url, data)

    def post(self, url, data):
        """Wrapper for aiohttp post.

        This method is a coroutine.
        """
        return self.request(aiohttp.hdrs.METH_POST, url, data)
