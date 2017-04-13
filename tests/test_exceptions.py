"""Tests for automatic exceptions."""
from aioautomatic import exceptions


def test_http_status_error_message():
    """Test custom message for http status error."""
    error = exceptions.ForbiddenError(
        "invalid_scope", "User has denied this scope.")
    assert str(error) == "invalid_scope: User has denied this scope."


def test_http_status_error_docstring():
    """Test that docstring is used as default message."""
    error = exceptions.UnauthorizedError()
    assert str(error) == "An invalid token is attached to the request."
