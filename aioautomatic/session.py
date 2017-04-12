"""Session interface for aioautomatic."""

import asyncio
import logging

from aioautomatic import base
from aioautomatic import const
from aioautomatic import data
from aioautomatic import validation

_LOGGER = logging.getLogger(__name__)


class Session(base.BaseApiObject):
    """Session object to manage access to a users information."""

    def __init__(self, client, **kwargs):
        """Create a session object."""
        super().__init__(client)
        self._client = client
        self._renew_handle = None
        self._load_token_data(**kwargs)

    def _load_token_data(self, access_token, refresh_token, expires_in, scope,
                         **kwargs):
        """Store the data from the access token response."""
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._scope = scope
        self._request_kwargs.update({
            'headers': {
                'Authorization': 'Bearer {}'.format(self._access_token),
            },
        })

        # Renew one hour before expiration
        renew_time = self.loop.time() + expires_in - 3600
        if self._renew_handle is not None:
            self._renew_handle.cancel()
        self._renew_handle = self.loop.call_at(
            renew_time, lambda: asyncio.ensure_future(self.refresh()))

    @asyncio.coroutine
    def refresh(self):
        """Use the refresh token to request a new access token."""
        _LOGGER.info("Refreshing the session access token.")
        auth_payload = {
            'client_id': self._client.client_id,
            'client_secret': self._client.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self._refresh_token,
        }
        resp = yield from self._post(const.AUTH_URL, auth_payload)
        resp = validation.AUTH_TOKEN(resp)
        self._load_token_data(**resp)

    @asyncio.coroutine
    def get_vehicles(self, **kwargs):
        """Get all vehicles associated with this user account.

        :param created_at__lte: Maximum start time filter
        :param created_at__gte: Minimum start time filter
        :param updated_at__lte: Maximum end time filter
        :param updated_at__gte: Minimum end time filter
        :param vin: Vin filter
        :param page: Page number of paginated result to return
        :param limit: Number of results per page
        """
        params = validation.VEHICLES_REQUEST(kwargs)
        querystring = '&'.join('{}={}'.format(k, v) for k, v in params.items())

        _LOGGER.info("Fetching vehicles.")
        resp = yield from self._get('?'.join((const.VEHICLE_URL, querystring)))
        return base.ResultList(self, resp, data.Vehicle)

    @asyncio.coroutine
    def get_trips(self, **kwargs):
        """Get all vehicles associated with this user account.

        :param started_at__lte: Maximum start time filter
        :param started_at__gte: Minimum start time filter
        :param ended_at__lte: Maximum end time filter
        :param ended_at__gte: Minimum end time filter
        :param vehicle: Vehicle Filter
        :param tags__in: Tags Filter
        :param page: Page number of paginated result to return
        :param limit: Number of results per page
        """
        params = validation.TRIPS_REQUEST(kwargs)
        querystring = '&'.join('{}={}'.format(k, v) for k, v in params.items())

        _LOGGER.info("Fetching trips.")
        resp = yield from self._get('?'.join((const.TRIP_URL, querystring)))
        return base.ResultList(self, resp, data.Trip)
