"""Tests for automatic validation."""
from datetime import datetime
from aioautomatic import validation

import pytest


def test_valid_timestamp(aiohttp_session):
    """Test that a valid datetime returns the timestamp."""
    dt = datetime(2017, 2, 21, 4, 35, 21, 123000)
    ts = validation.timestamp(dt)
    assert ts == 1487669721.123


def test_invalid_timestamp(aiohttp_session):
    """Test that a valid datetime returns the timestamp."""
    with pytest.raises(validation.vol.Invalid):
        validation.timestamp("test")
