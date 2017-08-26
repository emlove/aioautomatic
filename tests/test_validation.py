"""Tests for automatic validation."""
from datetime import datetime, timezone
from aioautomatic import validation
from aioautomatic import exceptions

import pytest


def test_valid_string_case_insensitive():
    """Test that strings are matched insesnsitive."""
    assert validation.string_case_insensitive("mock")("Mock") == "mock"
    assert validation.string_case_insensitive("mock")("Mock") == "mock"


def test_invalid_string_case_insensitive():
    """Test that nonmatching strings fail validation."""
    with pytest.raises(validation.vol.Invalid):
        assert validation.string_case_insensitive("Mock")("mock2")


def test_valid_timestamp():
    """Test that a valid datetime returns the timestamp."""
    dt = datetime(2017, 2, 21, 4, 35, 21, 123000, tzinfo=timezone.utc)
    ts = validation.timestamp(dt)
    assert ts == 1487651721.123


def test_invalid_timestamp():
    """Test that a valid datetime returns the timestamp."""
    with pytest.raises(validation.vol.Invalid):
        validation.timestamp("test")


def test_coerce_existing_datetime():
    """Test that a valid datetime is returned."""
    dt = datetime(2017, 2, 21, 4, 35, 21, 123000, tzinfo=timezone.utc)
    assert validation.coerce_datetime(dt) is dt


def test_parse_datetime():
    """Test that a valid string is parsed."""
    dt = datetime(2014, 3, 20, 1, 43, 36, 738000, tzinfo=timezone.utc)
    assert validation.coerce_datetime("2014-03-20T01:43:36.738000Z") == dt


def test_parse_datetime_no_ms():
    """Test that a valid string without milliseconds is parsed."""
    dt = datetime(2014, 3, 20, 1, 43, 36, tzinfo=timezone.utc)
    assert validation.coerce_datetime("2014-03-20T01:43:36Z") == dt


def test_invalid_datetime():
    """Test that an invalid string is not parsed."""
    with pytest.raises(validation.vol.DatetimeInvalid):
        validation.coerce_datetime("test")


def test_validate_schema():
    """Test that a valid message returns the correct object."""
    data = {
        "access_token": "mock_token",
        "expires_in": 2,
        "scope": "mock_scope",
        "refresh_token": "mock_refresah",
        "token_type": "bearer",
    }
    validated = validation.validate(validation.AUTH_TOKEN, data)

    assert data == validated


def test_validate_invalid_schema():
    """Test that an invalid message throws an exception."""
    data = {
        "access_token": None,
        "expires_in": 2,
        "scope": "mock_scope",
        "refresh_token": "mock_refresah",
        "token_type": "bearer",
    }
    with pytest.raises(exceptions.InvalidMessageError):
        validation.validate(validation.AUTH_TOKEN, data)
