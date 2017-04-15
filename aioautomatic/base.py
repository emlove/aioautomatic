"""Base interface for aioautomatic."""

import asyncio
import logging

import aiohttp

from aioautomatic import exceptions
from aioautomatic import validation

_LOGGER = logging.getLogger(__name__)


class BaseApiObject():
    """API object to perform network requests."""

    def __init__(self, parent, request_kwargs=None, client_session=None):
        """Create a base API object to send network requets."""
        self._parent = parent
        if parent is None:
            self._client_session = client_session or aiohttp.ClientSession()
            self._request_kwargs = request_kwargs or {}
        else:
            self._client_session = parent.client_session
            self._request_kwargs = parent.request_kwargs.copy()
            self._request_kwargs.update(request_kwargs or {})

    @asyncio.coroutine
    def _request(self, method, url, data):
        """Wrapper for aiohttp request that returns a parsed dict."""
        try:
            _LOGGER.debug('Sending %s, to %s: %s', method, url, data)
            resp = yield from self._client_session.request(
                method, url, data=data, **self._request_kwargs)
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
            raise exceptions.InvalidResponseError from exc

    def _get(self, url, data=None):
        """Wrapper for aiohttp get.

        This method is a coroutine.
        """
        return self._request(aiohttp.hdrs.METH_GET, url, data)

    def _post(self, url, data):
        """Wrapper for aiohttp post.

        This method is a coroutine.
        """
        return self._request(aiohttp.hdrs.METH_POST, url, data)

    @property
    def loop(self):
        """Active event loop for this object."""
        return self._client_session.loop

    @property
    def client_session(self):
        """Aiohttp client session for this object."""
        return self._client_session

    @property
    def request_kwargs(self):
        """kwargs that will be sent with each aiohttp request."""
        return self._request_kwargs


class BaseDataObject():
    """Object that represents data received from the API."""
    validator = lambda self, value: {}  # noqa: E731

    def __init__(self, data):
        """Create the data object."""
        self._data = self.validator(data)

    def __getattr__(self, name):
        """Lookup the attribute in the data dict."""
        try:
            return self._data[name]
        except KeyError as exc:
            raise AttributeError() from exc

    def __repr__(self):
        """Return a string representation of this object for debugging."""
        if not hasattr(self, 'id'):
            return super().__repr__()

        return '<{}.{} id="{}">'.format(
            self.__module__, self.__class__.__name__, self.id)


class ResultList(BaseApiObject, list):
    """List subclass to access list pages via the API."""

    def __init__(self, parent, resp, item_class):
        """Create a result list object."""
        BaseApiObject.__init__(self, parent)
        self._item_class = item_class
        resp = validation.LIST_RESPONSE(resp)
        list.__init__(self, (item_class(item) for item in resp['results']))
        self._next = resp['_metadata']['next']
        self._previous = resp['_metadata']['previous']

    @asyncio.coroutine
    def get_next(self):
        """Return the next set of results in the list."""
        if self._next is None:
            return None

        resp = yield from self._get(self._next)
        return ResultList(self._parent, resp, self._item_class)

    @asyncio.coroutine
    def get_previous(self):
        """Return the previous set of results in the list."""
        if self._previous is None:
            return None

        resp = yield from self._get(self._previous)
        return ResultList(self._parent, resp, self._item_class)

    @property
    def next(self):
        """Next url to be fetched in the list."""
        return self._next

    @property
    def previous(self):
        """Previous url to be fetched in the list."""
        return self._previous
