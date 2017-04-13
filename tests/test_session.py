"""Tests for automatic client."""
from datetime import datetime

from unittest.mock import MagicMock
from tests.common import AsyncMock


def test_session_refresh(session):
    """Test refreshing a session with the refresh token."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "access_token": "mock_access",
        "expires_in": 123456,
        "scope": ("scope:location scope:vehicle:profile "
                  "scope:user:profile scope:trip"),
        "refresh_token": "mock_refresh",
        "token_type": "Bearer",
    }
    session._client_session.request.return_value = resp
    refresh_token = session._refresh_token
    renew_handle = MagicMock()
    session._renew_handle = renew_handle
    session._client.client_id = "123"
    session._client.client_secret = "456"

    session.loop.run_until_complete(session.refresh())
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "POST"
    assert session._client_session.request.mock_calls[0][1][1] == \
        "https://accounts.automatic.com/oauth/access_token"
    assert session._client_session.request.mock_calls[0][2]['data'] == {
        "client_id": "123",
        "client_secret": "456",
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    assert renew_handle.cancel.called


def test_get_vehicles(session):
    """Test getting vehicle list."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "_metadata": {
            "count": 1,
            "next": None,
            "previous": None,
            },
        "results": [{
            "url": "mock_url",
            "id": "mock_id",
            "make": "mock_make",
            "model": "mock_model",
            "submodel": None,
            "created_at": "2015-03-20T01:43:36.738000Z",
            "fuel_level_percent": 73.9,
            }],
    }
    session._client_session.request.return_value = resp

    dt = datetime(2017, 1, 28)
    vehicle = session.loop.run_until_complete(
        session.get_vehicles(vin="VINVIN", created_at__gte=dt))[0]
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "GET"
    assert session._client_session.request.mock_calls[0][1][1][:34] == \
        "https://api.automatic.com/vehicle?"
    assert vehicle.url == "mock_url"
    assert vehicle.id == "mock_id"
    assert vehicle.make == "mock_make"
    assert vehicle.model == "mock_model"
    assert vehicle.vin is None
    assert vehicle.submodel is None
    assert vehicle.created_at == datetime(
        year=2015,
        month=3,
        day=20,
        hour=1,
        minute=43,
        second=36,
        microsecond=738000,
        )
    assert vehicle.fuel_level_percent == 73.9


def test_get_trips(session):
    """Test getting trip list."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "_metadata": {
            "count": 1,
            "next": None,
            "previous": None,
            },
        "results": [{
            "url": "mock_url",
            "id": "mock_id",
            "driver": "mock_driver",
            "user": "mock_user",
            "start_location": {
                "lat": 43.12345,
                "lon": 34.54321,
                "accuracy_m": 12.2,
                },
            "end_location": {
                "lat": 53.12345,
                "lon": 44.54321,
                "accuracy_m": 11.2,
                },
            "start_address": {
                "name": "123 Fake St",
                },
            "end_address": {
                "name": "456 Elm",
                },
            "hard_brakes": 2,
            "path": None,
            "started_at": "2015-03-21T01:43:36.738000Z",
            "ended_at": "2015-03-21T04:45:36.738000Z",
            "tags": ["business"],
            }],
    }
    session._client_session.request.return_value = resp

    dt = datetime(2017, 1, 28)
    trip = session.loop.run_until_complete(
        session.get_trips(vehicle="vehicle_id", started_at__gte=dt))[0]
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "GET"
    assert session._client_session.request.mock_calls[0][1][1][:31] == \
        "https://api.automatic.com/trip?"
    assert trip.url == "mock_url"
    assert trip.id == "mock_id"
    assert trip.driver == "mock_driver"
    assert trip.user == "mock_user"
    assert trip.fuel_cost_usd is None
    assert trip.start_location.lat == 43.12345
    assert trip.start_location.lon == 34.54321
    assert trip.start_location.accuracy_m == 12.2
    assert trip.end_location.lat == 53.12345
    assert trip.end_location.lon == 44.54321
    assert trip.end_location.accuracy_m == 11.2
    assert trip.start_address.name == "123 Fake St"
    assert trip.start_address.display_name is None
    assert trip.end_address.name == "456 Elm"
    assert trip.end_address.display_name is None
    assert trip.hard_brakes == 2
    assert trip.path is None
    assert trip.started_at == datetime(
        year=2015,
        month=3,
        day=21,
        hour=1,
        minute=43,
        second=36,
        microsecond=738000,
        )
    assert trip.ended_at == datetime(
        year=2015,
        month=3,
        day=21,
        hour=4,
        minute=45,
        second=36,
        microsecond=738000,
        )
    assert trip.tags == ["business"]
