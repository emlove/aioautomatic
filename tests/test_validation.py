"""Tests for automatic validation."""
from datetime import datetime, timezone
from aioautomatic import validation

import pytest


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
    """Test tahat an invalid string is not parsed."""
    with pytest.raises(validation.vol.DatetimeInvalid):
        validation.coerce_datetime("test")
