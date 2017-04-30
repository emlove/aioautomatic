"""Automatic API Exceptions."""


class AutomaticError(Exception):
    """Base class for all exceptions raised by this API."""


class ProtocolError(AutomaticError):
    """An error raised by Automatic caused by a protocol problem."""


class TransportError(AutomaticError):
    """An error caused by an underlying transport problem."""


class InvalidResponseError(ProtocolError):
    """The response returned from Automatic is not valid json."""


class SocketIOError(ProtocolError):
    """SocketIO error message received."""


class UnauthorizedClientError(SocketIOError):
    """Client is unauthorized for requested function."""


class HttpStatusError(ProtocolError):
    """Exception raised from the HTTP response status code."""

    def __init__(self, error=None, description=None):
        """Create an error for an http response status."""
        msg_list = list(filter(None, (error, description)))
        super().__init__(': '.join(msg_list) or self.__doc__)


class BadRequestError(HttpStatusError):
    """Request is malformed."""


class UnauthorizedError(HttpStatusError):
    """An invalid token is attached to the request."""


class ForbiddenError(HttpStatusError):
    """The token doesn't have access to the scope for this endpoint."""


class PageNotFoundError(HttpStatusError):
    """The specified endpoint cannot be found."""


class ConflictError(HttpStatusError):
    """Conflict in request."""


class UnprocessableDataError(HttpStatusError):
    """There is an issue processing the request body."""


class InternalError(HttpStatusError):
    """An internal error occurred at the Automatic server."""


# Exceptions to be raised based on HTTP status
HTTP_EXCEPTIONS = {
    400: BadRequestError,
    401: UnauthorizedError,
    403: ForbiddenError,
    404: PageNotFoundError,
    409: ConflictError,
    422: UnprocessableDataError,
    500: InternalError,
}

# Exceptions to be raised based on socketIO error messages
SOCKETIO_ERROR_EXCEPTIONS = {
    "Unauthorized client.": UnauthorizedClientError,
}


def get_socketio_error(msg=None):
    """Return a new socketIO error for the given message."""
    error = SOCKETIO_ERROR_EXCEPTIONS.get(msg, SocketIOError)
    return error(msg)
