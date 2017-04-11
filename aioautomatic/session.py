"""Session interface for aioautomatic."""

import asyncio
import datetime
import logging

from aioautomatic import const
from aioautomatic import validation

_LOGGER = logging.getLogger(__name__)


class Session():
    """Session object to manage access to a users information."""

    def __init__(self, client, **kwargs):
        """Create a session object."""
        self.client = client
        self.loop = client.loop
        self.renew_handle = None
        self._load_token_data(**kwargs)

    def _load_token_data(self, access_token, refresh_token, expires_in, scope,
                         **kwargs):
        """Store the data from the access token response."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.scope = scope
        self.expires = datetime.datetime.now() + \
            datetime.timedelta(seconds=expires_in)

        # Renew one hour before expiration
        renew_time = self.loop.time() + expires_in - 3600
        if self.renew_handle is not None:
            self.renew_handle.cancel()
        self.renew_handle = self.loop.call_at(
            renew_time, lambda: asyncio.ensure_future(self.refresh()))

    @asyncio.coroutine
    def refresh(self):
        """Use the refresh token to request a new access token."""
        _LOGGER.info("Refreshing the session access token.")
        auth_payload = {
            'client_id': self.client.client_id,
            'client_secret': self.client.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }
        resp = yield from self.client.post(const.AUTH_URL, auth_payload)
        resp = validation.AUTH_TOKEN(resp)
        self._load_token_data(**resp)
