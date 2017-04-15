"""Client interface for aioautomatic."""

import asyncio
import logging

from aioautomatic import base
from aioautomatic import const
from aioautomatic import exceptions
from aioautomatic import session
from aioautomatic import validation

_LOGGER = logging.getLogger(__name__)


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

    @asyncio.coroutine
    def create_session_from_password(self, username, password):
        """Create a session object authenticated by username and password.

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
            'scope': const.FULL_SCOPE,
            }
        try:
            resp = yield from self._post(const.AUTH_URL, auth_payload)
        except exceptions.ForbiddenError:
            auth_payload['scope'] = const.DEFAULT_SCOPE
            resp = yield from self._post(const.AUTH_URL, auth_payload)
            _LOGGER.debug("No client access to scope:current_location. "
                          "Live location updates not available.")
        resp = validation.AUTH_TOKEN(resp)
        return session.Session(self, **resp)

    @property
    def client_id(self):
        """Automatic Application Client ID"""
        return self._client_id

    @property
    def client_secret(self):
        """Automatic Application Secret"""
        return self._client_secret
